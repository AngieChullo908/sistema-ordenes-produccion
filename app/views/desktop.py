"""Vistas Tkinter: presentación y captura; no contienen SQL."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from app import __version__

STATES = ('Todos','Pendiente','En curso','Finalizado','Cancelado')

def table(parent, columns, widths=None):
    frame=ttk.Frame(parent)
    tree=ttk.Treeview(frame,columns=columns,show='headings',selectmode='browse',height=12)
    for i,col in enumerate(columns):
        tree.heading(col,text=col)
        tree.column(col,width=(widths or [140]*len(columns))[i],minwidth=65)
    bar=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
    horizontal=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview)
    tree.configure(yscrollcommand=bar.set,xscrollcommand=horizontal.set)
    tree.grid(row=0,column=0,sticky='nsew'); bar.grid(row=0,column=1,sticky='ns')
    horizontal.grid(row=1,column=0,sticky='ew')
    frame.rowconfigure(0,weight=1); frame.columnconfigure(0,weight=1)
    return frame,tree

def fill(tree, rows):
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert('', 'end', values=tuple('' if v is None else v for v in row))

class Dialog(tk.Toplevel):
    def __init__(self,parent,title):
        super().__init__(parent)
        self.title(title); self.transient(parent)
        self.body=ttk.Frame(self,padding=20); self.body.pack(fill='both',expand=True)
        self.result=None
        self.protocol('WM_DELETE_WINDOW',self.destroy)
        self.bind('<Escape>',lambda e:self.destroy())
        self.after_idle(self.grab_set)

class ConnectionDialog(Dialog):
    def __init__(self,parent,settings,submit):
        super().__init__(parent,'Conectar con PostgreSQL · Gestión de Órdenes de Producción')
        self.resizable(False,False)
        ttk.Label(self.body,text='Conexión a la base de datos',style='Title.TLabel').grid(row=0,column=0,columnspan=2,pady=(0,15))
        self.values={}
        fields=[('host','Servidor'),('port','Puerto'),('dbname','Base de datos'),('user','Usuario'),('password','Contraseña'),('sslmode','SSL')]
        for i,(key,label) in enumerate(fields,1):
            ttk.Label(self.body,text=label).grid(row=i,column=0,sticky='w',pady=5,padx=(0,12))
            var=tk.StringVar(value=settings.get(key,'')); self.values[key]=var
            if key=='sslmode':
                widget=ttk.Combobox(self.body,textvariable=var,values=('prefer','require','verify-full','disable'),state='readonly')
            else:
                widget=ttk.Entry(self.body,textvariable=var,width=34,show='●' if key=='password' else '')
            widget.grid(row=i,column=1,sticky='ew')
        ttk.Label(self.body,text='La contraseña se conserva solo durante esta sesión.').grid(row=7,column=0,columnspan=2,pady=12)
        self.button=ttk.Button(self.body,text='Conectar',command=lambda:submit(self))
        self.button.grid(row=8,column=0,columnspan=2,sticky='ew')
        self.bind('<Return>',lambda e:submit(self))

class MainView:
    def __init__(self,root):
        self.root=root; root.title(f'Gestión de Órdenes de Producción {__version__}'); root.geometry('1180x800'); root.minsize(960,620)
        style=ttk.Style(root); style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10))
        style.configure('Title.TLabel',font=('Segoe UI',16,'bold'),foreground='#183c36')
        style.configure('Treeview',rowheight=29); style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'))
        style.configure('TButton',padding=(12,7)); style.configure('TNotebook.Tab',padding=(18,9))
        outer=ttk.Frame(root,padding=20); outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='Gestión de Órdenes de Producción',style='Title.TLabel',wraplength=1000,justify='left').pack(anchor='w')
        ttk.Label(outer,text='Programa la jornada, consulta las recetas y registra los resultados.').pack(anchor='w',pady=(3,16))
        self.book=ttk.Notebook(outer); self.book.pack(fill='both',expand=True)
        orders=ttk.Frame(self.book,padding=12); self.book.add(orders,text='Órdenes')
        filters=ttk.Frame(orders); filters.pack(fill='x',pady=(0,10))
        self.search=tk.StringVar(); self.state=tk.StringVar(value='Todos')
        ttk.Label(filters,text='Orden o responsable').pack(side='left')
        self.search_box=ttk.Entry(filters,textvariable=self.search,width=30); self.search_box.pack(side='left',padx=8)
        ttk.Combobox(filters,textvariable=self.state,values=STATES,state='readonly',width=13).pack(side='left')
        self.search_button=ttk.Button(filters,text='Buscar'); self.search_button.pack(side='left',padx=8)
        self.new_button=ttk.Button(filters,text='+ Nueva orden'); self.new_button.pack(side='right')
        frame,self.orders=table(orders,('Orden','Fecha','Responsable','Estado','Productos','Unidades'),[125,120,220,125,100,100]); frame.pack(fill='both',expand=True)
        actions=ttk.Frame(orders); actions.pack(fill='x',pady=10)
        self.buttons={}
        for key,text in [('detail','Ver detalle'),('edit','Editar'),('start','Iniciar'),('close','Registrar cierre'),('cancel','Cancelar'),('delete','Eliminar'),('export','Exportar CSV')]:
            button=ttk.Button(actions,text=text); button.pack(side='left',padx=(0,6)); self.buttons[key]=button
        products=ttk.Frame(self.book,padding=12); self.book.add(products,text='Productos y recetas')
        ttk.Label(products,text='Seleccione un producto para consultar su preparación e ingredientes.').pack(anchor='w',pady=(0,8))
        frame,self.products=table(products,('Código','Producto','Categoría','Stock','Unidad','Precio S/','Receta'),[85,230,120,80,80,95,120]); frame.pack(fill='both',expand=True)
        self.recipe_button=ttk.Button(products,text='Consultar receta'); self.recipe_button.pack(anchor='w',pady=10)
        ingredients=ttk.Frame(self.book,padding=12); self.book.add(ingredients,text='Existencias de insumos')
        frame,self.ingredients=table(ingredients,('Código','Ingrediente','Stock','Unidad'),[100,360,160,100]); frame.pack(fill='both',expand=True)
        ttk.Label(ingredients,text='Las existencias se muestran en la unidad de medida de cada ingrediente.').pack(anchor='w',pady=10)
        reports=ttk.Frame(self.book,padding=12); self.book.add(reports,text='10 reportes')
        from app.infrastructure.reports import REPORTS
        bar=ttk.Frame(reports); bar.pack(fill='x',pady=(0,12))
        self.report_choice=tk.StringVar(value='1. '+REPORTS[0][0])
        self.report_selector=ttk.Combobox(bar,textvariable=self.report_choice,values=[str(i+1)+'. '+r[0] for i,r in enumerate(REPORTS)],state='readonly',width=55)
        self.report_selector.pack(side='left')
        self.report_parameter=tk.StringVar()
        self.report_parameter_entry=ttk.Entry(bar,textvariable=self.report_parameter,width=13,state='disabled')
        self.report_parameter_entry.pack(side='left',padx=8)
        self.report_button=ttk.Button(bar,text='Consultar'); self.report_button.pack(side='left')
        self.report_export=ttk.Button(bar,text='Exportar CSV'); self.report_export.pack(side='right')
        ttk.Label(reports,text='Parámetro: reporte 3 usa una orden (OP000010); reporte 6 usa una receta (R001). Los demás no requieren parámetro.').pack(anchor='w',pady=(0,8))
        self.report_area=ttk.Frame(reports); self.report_area.pack(fill='both',expand=True)
        self.status=tk.StringVar(value='Conecte con PostgreSQL para comenzar.')
        ttk.Label(outer,textvariable=self.status).pack(anchor='w',pady=(12,0))
        self.refresh_button=ttk.Button(outer,text='Actualizar datos'); self.refresh_button.pack(anchor='e')

    def selected(self):
        selected=self.orders.selection()
        return self.orders.item(selected[0],'values')[0] if selected else None

class OrderDialog(Dialog):
    def __init__(self,parent,catalog,submit,header=None,lines=None):
        super().__init__(parent,'Editar orden pendiente' if header else 'Nueva orden de producción')
        self.geometry('800x540'); self.number=header['numero_orden'] if header else None
        self.employee_map={f"{e['codigo_empleado']} · {e['nombre_empleado']} ({e['cargo_empleado']})":e['codigo_empleado'] for e in catalog['employees']}
        self.product_map={f"{p['cod_producto']} · {p['nombre_producto']}":p['cod_producto'] for p in catalog['products']}
        top=ttk.Frame(self.body); top.pack(fill='x')
        ttk.Label(top,text='Fecha (AAAA-MM-DD)').grid(row=0,column=0,sticky='w')
        self.day=tk.StringVar(value=str(header['fecha_prog']) if header else date.today().isoformat())
        ttk.Entry(top,textvariable=self.day,width=16).grid(row=1,column=0,padx=(0,15),pady=6)
        ttk.Label(top,text='Responsable').grid(row=0,column=1,sticky='w')
        self.employee=tk.StringVar(value=next((k for k,v in self.employee_map.items() if header and v==header['codigo_empleado']),''))
        ttk.Combobox(top,textvariable=self.employee,values=list(self.employee_map),state='readonly',width=48).grid(row=1,column=1,sticky='w')
        add=ttk.Frame(self.body); add.pack(fill='x',pady=15)
        self.product=tk.StringVar(); self.quantity=tk.StringVar(value='1')
        ttk.Combobox(add,textvariable=self.product,values=list(self.product_map),state='readonly',width=37).pack(side='left')
        ttk.Entry(add,textvariable=self.quantity,width=7).pack(side='left',padx=8)
        ttk.Button(add,text='Agregar / cambiar cantidad',command=self.add).pack(side='left')
        footer=ttk.Frame(self.body)
        footer.pack(side='bottom',fill='x',pady=(10,0))
        ttk.Button(footer,text='Quitar producto seleccionado',command=self.remove).pack(side='left')
        self.save_button=ttk.Button(footer,text='Guardar orden',command=lambda:submit(self))
        self.save_button.pack(side='right')
        frame,self.tree=table(self.body,('Código','Producto','Cantidad'),[100,380,120]); frame.pack(fill='both',expand=True)
        for line in lines or []:
            self.tree.insert('','end',iid=line['cod_producto'],values=(line['cod_producto'],line['nombre_producto'],line['cant_programada']))
        self.tree.bind('<<TreeviewSelect>>',self.select)

    def add(self):
        from app.models.order import integer, BusinessError
        try:
            code=self.product_map.get(self.product.get())
            if not code: raise BusinessError('Seleccione un producto.')
            qty=integer(self.quantity.get(),'Cantidad',1)
            values=(code,self.product.get().split(' · ',1)[1],qty)
            if self.tree.exists(code): self.tree.item(code,values=values)
            else: self.tree.insert('','end',iid=code,values=values)
        except BusinessError as exc: messagebox.showerror('Datos inválidos',str(exc),parent=self)

    def select(self,event):
        if self.tree.selection():
            code=self.tree.selection()[0]
            self.product.set(next(k for k,v in self.product_map.items() if v==code))
            self.quantity.set(self.tree.item(code,'values')[2])

    def remove(self):
        for item in self.tree.selection(): self.tree.delete(item)

class CloseDialog(Dialog):
    """Formulario adaptable: las columnas siguen el ancho del área visible."""

    def __init__(self, parent, number, lines, submit):
        super().__init__(parent, f'Cierre · {number}')
        self.number = number
        self.rows = []
        self._product_labels = []
        self.minsize(840, 380)
        width = max(840, min(1060, self.winfo_screenwidth() - 100))
        height = max(380, min(self.winfo_screenheight() - 140,
                              max(440, min(len(lines), 9) * 42 + 230)))
        self.geometry(f'{width}x{height}')

        ttk.Label(self.body, text='Registra la producción real',
                  style='Title.TLabel').pack(anchor='w')
        guidance = ttk.Label(
            self.body,
            text='Producida + perdida = programada. Indique un motivo por cada merma.',
            wraplength=width - 50,
        )
        guidance.pack(anchor='w', pady=8)
        self.body.bind('<Configure>', lambda event: guidance.configure(
            wraplength=max(300, event.width - 12)))

        footer = ttk.Frame(self.body)
        footer.pack(side='bottom', fill='x', pady=(10, 0))
        warning = ttk.Label(
            footer,
            text='Al cerrar se sumará la cantidad producida al stock de productos. '
                 'El cierre es definitivo.',
            wraplength=width - 50,
        )
        warning.pack(anchor='w', pady=(0, 8))
        footer.bind('<Configure>', lambda event: warning.configure(
            wraplength=max(300, event.width - 12)))
        self.save_button = ttk.Button(
            footer, text='Confirmar cierre definitivo', command=lambda: submit(self))
        self.save_button.pack(anchor='e')

        area = ttk.Frame(self.body)
        area.pack(fill='both', expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        background = ttk.Style(self).lookup('TFrame', 'background') or '#dcdad5'
        self.canvas = tk.Canvas(area, highlightthickness=0, borderwidth=0,
                                background=background)
        self.scrollbar = ttk.Scrollbar(area, orient='vertical',
                                       command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._set_scrollbar)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.content = ttk.Frame(self.canvas)
        self._content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor='nw')
        self.content.columnconfigure(0, weight=2, minsize=225)
        for column in (1, 2, 3):
            self.content.columnconfigure(column, weight=0, minsize=88)
        self.content.columnconfigure(4, weight=3, minsize=250)
        self.canvas.bind('<Configure>', self._fit_content)
        self.content.bind('<Configure>', self._update_scrollregion)

        headers = ('Producto', 'Programada', 'Producida', 'Perdida', 'Motivo (máx. 80)')
        for column, text in enumerate(headers):
            ttk.Label(self.content, text=text).grid(
                row=0, column=column, padx=7, pady=8,
                sticky='w' if column in (0, 4) else '')
        for row, line in enumerate(lines, 1):
            produced = tk.StringVar(value=str(line['cant_programada']))
            lost = tk.StringVar(value='0')
            reason = tk.StringVar()
            product = ttk.Label(
                self.content,
                text=f"{line['cod_producto']} · {line['nombre_producto']}",
                wraplength=210,
            )
            product.grid(row=row, column=0, padx=7, pady=9, sticky='w')
            self._product_labels.append(product)
            ttk.Label(self.content, text=line['cant_programada']).grid(
                row=row, column=1, padx=7, pady=9)
            for column, variable, entry_width in (
                    (2, produced, 8), (3, lost, 8), (4, reason, 28)):
                ttk.Entry(self.content, textvariable=variable,
                          width=entry_width).grid(
                              row=row, column=column, padx=7, pady=9, sticky='ew')
            self.rows.append((line['cod_producto'], produced, lost, reason))

        for widget in (self.canvas, self.content, *self.content.winfo_children()):
            widget.bind('<MouseWheel>', self._mousewheel)
            widget.bind('<Button-4>', self._mousewheel)
            widget.bind('<Button-5>', self._mousewheel)

    def _fit_content(self, event):
        self.canvas.itemconfigure(self._content_window, width=event.width)
        self._update_scrollregion()

    def _update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=(
            0, 0, self.canvas.winfo_width(),
            max(self.content.winfo_reqheight(), self.canvas.winfo_height())))
        # Limitar el ajuste de línea a la columna del producto, sin ensancharla.
        product_width = max(150, min(320, self.content.grid_bbox(0, 0)[2] - 14))
        for label in self._product_labels:
            if int(label.cget('wraplength')) != product_width:
                label.configure(wraplength=product_width)

    def _set_scrollbar(self, first, last):
        self.scrollbar.set(first, last)
        if float(first) <= 0 and float(last) >= 1:
            self.scrollbar.grid_remove()
        else:
            self.scrollbar.grid()

    def _mousewheel(self, event):
        if getattr(event, 'num', None) == 4:
            steps = -1
        elif getattr(event, 'num', None) == 5:
            steps = 1
        else:
            delta = getattr(event, 'delta', 0)
            if not delta:
                return
            steps = int(-delta / 120) or (-1 if delta > 0 else 1)
        self.canvas.yview_scroll(steps, 'units')
        return 'break'
