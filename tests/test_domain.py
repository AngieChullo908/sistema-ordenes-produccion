import unittest
from app.models.order import *

class DomainTests(unittest.TestCase):
    def test_valid_order(self):
        validate_order('2026-11-10','E001',[OrderLine('P001',4)])
    def test_bad_date(self):
        with self.assertRaises(BusinessError): validate_order('2026-02-30','E001',[OrderLine('P001',4)])
    def test_empty_order(self):
        with self.assertRaises(BusinessError): validate_order('2026-11-10','E001',[])
    def test_duplicate_product(self):
        with self.assertRaises(BusinessError): validate_order('2026-11-10','E001',[OrderLine('P001',2),OrderLine('P001',3)])
    def test_bad_quantities(self):
        for value in ('1.2','-1','1000','NaN','١',True):
            with self.subTest(value=value),self.assertRaises(BusinessError): integer(value,'Cantidad',1)
    def test_valid_close(self):
        validate_close({'P001':5},[FinalLine('P001',4,1,'Quemado')])
    def test_close_mismatch(self):
        with self.assertRaises(BusinessError): validate_close({'P001':5},[FinalLine('P001',3,1,'Quemado')])
    def test_merma_reason(self):
        with self.assertRaises(BusinessError): validate_close({'P001':5},[FinalLine('P001',4,1,'')])
    def test_missing_product(self):
        with self.assertRaises(BusinessError): validate_close({'P001':5,'P002':3},[FinalLine('P001',5,0)])
    def test_duplicate_close(self):
        with self.assertRaises(BusinessError): validate_close({'P001':5},[FinalLine('P001',5,0),FinalLine('P001',5,0)])
    def test_reason_without_loss(self):
        with self.assertRaises(BusinessError): validate_close({'P001':5},[FinalLine('P001',5,0,'Motivo')])
    def test_start_delegates_order_state_change(self):
        called=[]
        class Fake:
            def start(self,number): called.append(number)
        ProductionService(Fake()).start('OP000001')
        self.assertEqual(called,['OP000001'])

if __name__=='__main__': unittest.main()
