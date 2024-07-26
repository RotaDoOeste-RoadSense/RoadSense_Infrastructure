from ultralytics import YOLO
import glob,re
class OCR:
    model_path = '/home/mateus/ocr/VICTOR/Fluxo_obtencao_kilometros/best_ocr.pt'
    model = YOLO(model_path)
    def inference(self,image_path):
        _ = self.model(image_path)[0].boxes
        _ = self.filter_result_boxes(_)
        _ = self.order_boxes_by_x(_)
        if _['lower']>1200:
            self._last_inference = None
            return
        self._last_inference = _
        return _
    def filter_result_boxes(self,boxes):
        out_boxes = {'upper':[],'lower':[]}
        for box in boxes:
            if box.xyxyn[0][1]>0.5:
                out_boxes['lower'].append(box)
            else:
                out_boxes['upper'].append(box)
        return out_boxes
    def order_boxes_by_x(self,boxes_dict):
        order_dict = {}
        for key,_list in boxes_dict.items():
            boxes = sorted(_list,key=lambda a:a.xyxyn[0][0])
            order_dict[key] = boxes
        return order_dict
    def convert_class_to_name(self,class_id):
        return self.model.names[class_id]
    def get_inference(self):
        if self._last_inference:
            upper = ''.join([str(self.convert_class_to_name(int(_.cls[0]))) for _ in self._last_inference['upper']])
            lower = ''.join([str(self.convert_class_to_name(int(_.cls[0]))) for _ in self._last_inference['lower']])
            return {'upper':upper,'lower':lower}
ocr = OCR()
def make_inference(image):
    ocr.inference(image)
    return ocr.get_inference()