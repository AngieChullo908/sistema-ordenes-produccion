import csv
import logging
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg
from app.models.order import ProductionService, OrderLine, FinalLine, BusinessError, integer
from app.infrastructure.postgres import ConnectionFactory, PostgresRepository
from app.infrastructure import settings
from app.views.desktop import MainView, ConnectionDialog, OrderDialog, CloseDialog, Dialog, table, fill

class ProductionController:
    def __init__(self,root):
        self.root=root; self.view=MainView(root); self.repository=None; self.catalog=None; self.busy=False
        self.events=queue.Queue(); root.after(75,self.poll)
        v=self.view
        v.new_button.configure(command=self.new)
        v.search_button.configure(command=self.refresh)
        v.search_box.bind('<Return>',lambda e:self.refresh())
        v.refresh_button.configure(command=self.refresh)
        for key,handler in [('detail',self.detail),('edit',self.edit),('start',self.start),('close',self.close),('cancel',self.cancel),('delete',self.delete),('export',self.export)]:
            v.buttons[key].configure(command=handler)
        v.orders.bind('<Double-1>',lambda e:self.detail())
        self.report_generation=0
        v.report_selector.bind('<<ComboboxSelected>>',self.report_changed)
        v.report_button.configure(command=self.report)
        v.report_export.configure(command=self.export_report)
        v.recipe_button.configure(command=self.recipe)
        v.products.bind('<Double-1>',lambda e:self.recipe())
        root.after(100,lambda:ConnectionDialog(root,settings.load(),self.connect))

    def poll(self):
        try:
            while True:
                ok,value,callback=self.events.get_nowait()
                self.busy=False; self.view.status.set('Listo.')
                if ok:
                    callback(value)
                else: self.error(value)
        except queue.Empty: pass
        self.root.after(75,self.poll)

    def task(self,work,callback=lambda value:None):
        if self.busy:
            messagebox.showinfo('Operación en curso','Espere a que termine la operación actual.',parent=self.root); return
        self.busy=True; self.view.status.set('Procesando…')
        def run():
            try: self.events.put((True,work(),callback))
            except Exception as exc: self.events.put((False,exc,callback))
        threading.Thread(target=run,daemon=True).start()

    def error(self,exc):
        if isinstance(exc,BusinessError): text=str(exc)
        elif isinstance(exc,psycopg.errors.UniqueViolation): text='Ya existe un registro con esa clave. Revise las secuencias si se cargaron códigos manualmente.'
        elif isinstance(exc,psycopg.errors.ForeignKeyViolation): text='Un producto o responsable dejó de estar disponible. Actualice los datos.'
        elif isinstance(exc,psycopg.errors.CheckViolation): text='Los datos exceden una restricción de la base de datos.'
        elif isinstance(exc,psycopg.errors.UndefinedTable): text='Faltan tablas. Ejecute los scripts de instalación en la base de datos seleccionada.'
        elif isinstance(exc,psycopg.OperationalError): text='No se pudo completar la conexión. Revise servidor, puerto, credenciales y servicio PostgreSQL; si hubo una interrupción, actualice el historial antes de repetir una operación.'
        elif isinstance(exc,psycopg.Error): text='PostgreSQL rechazó la operación (código '+str(exc.sqlstate or 'sin código')+'). Actualice y consulte con el administrador.'
        else: text='No se pudo completar la operación. Consulte el archivo de diagnóstico.'
        # No registrar SQL, parámetros ni credenciales.
        logging.error('Tipo de error: %s; SQLSTATE=%s',type(exc).__name__,getattr(exc,'sqlstate',None))
        messagebox.showerror('Gestión de Órdenes de Producción',text,parent=self.root)

    def connect(self,dialog):
        values={k:v.get() for k,v in dialog.values.items()}
        try:
            integer(values['port'],'Puerto',1,65535)
            if not all(values[k].strip() for k in ('host','dbname','user')): raise BusinessError('Complete servidor, base de datos y usuario.')
        except BusinessError as exc: self.error(exc); return
        repository=PostgresRepository(ConnectionFactory(values))
        def connected(_):
            self.repository=repository; self.service=ProductionService(repository); settings.save(values)
            if dialog.winfo_exists(): dialog.destroy()
            self.refresh()
        self.task(repository.check,connected)

    def ready(self):
        if not self.repository:
            ConnectionDialog(self.root,settings.load(),self.connect); return False
        return True

    def refresh(self):
        if not self.ready(): return
        search,state=self.view.search.get(),self.view.state.get()
        self.task(lambda:(self.repository.catalog(),self.repository.orders(search,state)),self.render)

    def render(self,data):
        self.catalog,rows=data; self.order_rows=rows
        fill(self.view.orders,[(r['numero_orden'],r['fecha_prog'],r['nombre_empleado'],r['estado'],r['productos'],r['unidades']) for r in rows])
        fill(self.view.products,[(p['cod_producto'],p['nombre_producto'],p['nombre_categoria'],p['stock'],p['simbolo'],p['precio'],p['cod_receta']) for p in self.catalog['products']])
        fill(self.view.ingredients,[(i['cod_ingrediente'],i['nombre_ingredientes'],i['stock_ingrediente'],i['simbolo']) for i in self.catalog['ingredients']])
        self.view.status.set(f'{len(rows)} órdenes encontradas · PostgreSQL conectado')

    def selected(self):
        if not self.ready(): return None
        number=self.view.selected()
        if not number: messagebox.showinfo('Seleccione una orden','Seleccione una fila de la lista.',parent=self.root)
        return number

    def new(self):
        if not self.ready() or not self.catalog: return
        OrderDialog(self.root,self.catalog,self.save_order)

    def edit(self):
        number=self.selected()
        if number:
            def show(data):
                header,lines=data
                if header['estado']!='Pendiente': raise BusinessError('Solo puede editar órdenes pendientes.')
                OrderDialog(self.root,self.catalog,self.save_order,header,lines)
            self.task(lambda:self.repository.detail(number),self.safe(show))

    def safe(self,callback):
        def wrapped(value):
            try: callback(value)
            except Exception as exc: self.error(exc)
        return wrapped

    def save_order(self,dialog):
        try:
            lines=[OrderLine(dialog.tree.item(x,'values')[0],int(dialog.tree.item(x,'values')[2])) for x in dialog.tree.get_children()]
            day=dialog.day.get().strip(); employee=dialog.employee_map.get(dialog.employee.get(),'')
            from app.models.order import validate_order
            validate_order(day,employee,lines)
        except BusinessError as exc: self.error(exc); return
        self.task(lambda:self.service.save(dialog.number,day,employee,lines),lambda number:self.saved(dialog,f'Orden {number} guardada.'))

    def saved(self,dialog,text):
        if dialog and dialog.winfo_exists(): dialog.destroy()
        messagebox.showinfo('Operación completada',text,parent=self.root); self.refresh()

    def start(self):
        number=self.selected()
        if number and messagebox.askyesno('Iniciar producción',f'¿Iniciar la orden {number}?',parent=self.root):
            self.task(lambda:self.service.start(number),lambda _:self.saved(None,'Producción iniciada.'))

    def cancel(self):
        number=self.selected()
        if number and messagebox.askyesno('Cancelar orden',f'¿Cancelar {number}? Solo se cancelan órdenes pendientes. El registro se conserva en el historial.',parent=self.root):
            self.task(lambda:self.service.cancel(number),lambda _:self.saved(None,'Orden cancelada.'))

    def close(self):
        number=self.selected()
        if number:
            def show(data):
                if data[0]['estado']!='En curso': raise BusinessError('Solo puede cerrar órdenes en curso.')
                CloseDialog(self.root,number,data[1],self.save_close)
            self.task(lambda:self.repository.detail(number),self.safe(show))

    def save_close(self,dialog):
        try:
            results=[FinalLine(code,integer(produced.get(),'Producida'),integer(lost.get(),'Perdida'),reason.get().strip()) for code,produced,lost,reason in dialog.rows]
        except BusinessError as exc: self.error(exc); return
        if not messagebox.askyesno('Confirmación de cierre','¿Guardar definitivamente el cierre y sumar los productos aptos al inventario?',parent=dialog): return
        self.task(lambda:self.service.close(dialog.number,results),lambda _:self.saved(dialog,'Cierre guardado e inventario de productos actualizado.'))

    def detail(self):
        number=self.selected()
        if number:
            def show(data):
                header,lines=data; dialog=Dialog(self.root,number+' · Detalle'); dialog.geometry('1000x490')
                ttk.Label(dialog.body,text=number,style='Title.TLabel').pack(anchor='w')
                ttk.Label(dialog.body,text=f"{header['fecha_prog']} · {header['nombre_empleado']} / {header['cargo_empleado']} · {header['estado']}\nResultado: {header['resultado'] or 'Sin cierre'}").pack(anchor='w',pady=12)
                frame,tree=table(dialog.body,('Producto','Programada','Producida','Perdida','Motivo'),[240,110,110,110,330]); frame.pack(fill='both',expand=True)
                fill(tree,[(x['nombre_producto'],x['cant_programada'],x['cant_producida'],x['cant_perdida'],x['descripcion_perdida']) for x in lines])
            self.task(lambda:self.repository.detail(number),show)

    def recipe(self):
        if not self.ready() or not self.catalog: return
        selection=self.view.products.selection()
        if not selection:
            messagebox.showinfo('Seleccione un producto','Seleccione un producto de la lista.',parent=self.root); return
        code=self.view.products.item(selection[0],'values')[0]
        product=next(p for p in self.catalog['products'] if p['cod_producto']==code)
        def show(rows):
            dialog=Dialog(self.root,product['nombre_receta']); dialog.geometry('940x620')
            ttk.Label(dialog.body,text=product['nombre_receta'],style='Title.TLabel').pack(anchor='w')
            text=tk.Text(dialog.body,height=7,wrap='word',font=('Segoe UI',10)); text.pack(fill='x',pady=10)
            text.insert('1.0',product['preparacion']); text.configure(state='disabled')
            frame,tree=table(dialog.body,('Ingrediente','Cantidad receta','Unidad receta','Stock','Unidad stock'),[270,130,120,130,120]); frame.pack(fill='both',expand=True)
            fill(tree,[(x['nombre_ingredientes'],x['cant_requerida'],x['simbolo'],x['stock_ingrediente'],x['unidad_stock']) for x in rows])
            ttk.Label(dialog.body,text='Cantidades de la receta seleccionada.\nRevise la unidad indicada en cada columna.').pack(anchor='w',pady=12)
        self.task(lambda:self.repository.recipe(product['cod_receta']),show)

    def export(self):
        if not self.ready() or not hasattr(self,'order_rows'): return
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.csv',initialfile='ordenes_avecesar.csv',filetypes=[('CSV','*.csv')])
        if not path: return
        def safe(value):
            value=str(value)
            return "'"+value if value.startswith(('=','+','-','@','\t','\r','\n')) else value
        try:
            with open(path,'w',encoding='utf-8-sig',newline='') as file:
                writer=csv.writer(file,delimiter=';'); writer.writerow(('Orden','Fecha','Responsable','Estado','Productos','Unidades'))
                for row in self.order_rows:
                    writer.writerow([safe(row[key]) for key in ('numero_orden','fecha_prog','nombre_empleado','estado','productos','unidades')])
            messagebox.showinfo('Exportación','CSV guardado con los filtros actuales.',parent=self.root)
        except OSError: messagebox.showerror('Exportación','No se pudo escribir el archivo. Revise permisos o cierre Excel.',parent=self.root)

    def delete(self):
        number=self.selected()
        if number and messagebox.askyesno('Eliminar orden pendiente',f'¿Eliminar definitivamente {number} y sus detalles? Esta operación no se puede deshacer.',parent=self.root):
            self.task(lambda:self.repository.delete(number),lambda _:self.saved(None,'Orden pendiente eliminada.'))

    def report_changed(self,event=None):
        self.report_generation+=1
        index=int(self.view.report_choice.get().split('.',1)[0])-1
        needs=index in (2,5)
        self.view.report_parameter_entry.configure(state='normal' if needs else 'disabled')
        self.view.report_parameter.set('OP000010' if index==2 else 'R001' if index==5 else '')
        if hasattr(self,'report_data'): del self.report_data
        for child in self.view.report_area.winfo_children(): child.destroy()
        self.view.status.set('Seleccione Consultar para obtener el reporte.')

    def report(self):
        if not self.ready(): return
        index=int(self.view.report_choice.get().split('.',1)[0])-1
        parameter=self.view.report_parameter.get().strip()
        generation=self.report_generation
        def show(result):
            if generation!=self.report_generation: return
            columns,rows=result; self.report_data=(columns,rows)
            for child in self.view.report_area.winfo_children(): child.destroy()
            frame,tree=table(self.view.report_area,columns); frame.pack(fill='both',expand=True)
            fill(tree,[[row[c] for c in columns] for row in rows])
            self.view.status.set(f'Reporte {index+1}: {len(rows)} registros')
        self.task(lambda:self.repository.report(index,parameter),show)

    def export_report(self):
        if not hasattr(self,'report_data'):
            messagebox.showinfo('Reportes','Consulte primero un reporte.',parent=self.root); return
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.csv',initialfile='reporte_avecesar.csv',filetypes=[('CSV','*.csv')])
        if not path: return
        columns,rows=self.report_data
        def safe(value):
            text='' if value is None else str(value)
            return "'"+text if text.startswith(('=','+','-','@','\t','\r','\n')) else text
        try:
            with open(path,'w',encoding='utf-8-sig',newline='') as file:
                writer=csv.writer(file,delimiter=';'); writer.writerow(columns)
                writer.writerows([[safe(row[col]) for col in columns] for row in rows])
            messagebox.showinfo('Exportación','Reporte CSV guardado.',parent=self.root)
        except OSError: messagebox.showerror('Exportación','No se pudo guardar el CSV.',parent=self.root)
