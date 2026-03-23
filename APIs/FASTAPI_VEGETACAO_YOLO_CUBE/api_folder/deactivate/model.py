import cv2
import numpy as np
import torch
import cv2
import numpy as np
import onnxruntime as ort
import torch
from tqdm import tqdm
import torch
import numpy as np
from functools import lru_cache
import cv2
import time
import torch.nn.functional as F
import ast
import torchvision.transforms as T
from PIL import Image



class LetterBox:
    """
    Resize image and padding for detection, instance segmentation, pose.

    This class resizes and pads images to a specified shape while preserving aspect ratio. It also updates
    corresponding labels and bounding boxes.

    Attributes:
        new_shape (tuple): Target shape (height, width) for resizing.
        auto (bool): Whether to use minimum rectangle.
        scaleFill (bool): Whether to stretch the image to new_shape.
        scaleup (bool): Whether to allow scaling up. If False, only scale down.
        stride (int): Stride for rounding padding.
        center (bool): Whether to center the image or align to top-left.

    Methods:
        __call__: Resize and pad image, update labels and bounding boxes.

    Examples:
        >>> transform = LetterBox(new_shape=(640, 640))
        >>> result = transform(labels)
        >>> resized_img = result["img"]
        >>> updated_instances = result["instances"]
    """

    def __init__(self, new_shape=(640, 640), auto=False, scaleFill=False, scaleup=True, center=True, stride=32):
        """
        Initialize LetterBox object for resizing and padding images.

        This class is designed to resize and pad images for object detection, instance segmentation, and pose estimation
        tasks. It supports various resizing modes including auto-sizing, scale-fill, and letterboxing.

        Args:
            new_shape (Tuple[int, int]): Target size (height, width) for the resized image.
            auto (bool): If True, use minimum rectangle to resize. If False, use new_shape directly.
            scaleFill (bool): If True, stretch the image to new_shape without padding.
            scaleup (bool): If True, allow scaling up. If False, only scale down.
            center (bool): If True, center the placed image. If False, place image in top-left corner.
            stride (int): Stride of the model (e.g., 32 for YOLOv5).

        Attributes:
            new_shape (Tuple[int, int]): Target size for the resized image.
            auto (bool): Flag for using minimum rectangle resizing.
            scaleFill (bool): Flag for stretching image without padding.
            scaleup (bool): Flag for allowing upscaling.
            stride (int): Stride value for ensuring image size is divisible by stride.

        Examples:
            >>> letterbox = LetterBox(new_shape=(640, 640), auto=False, scaleFill=False, scaleup=True, stride=32)
            >>> resized_img = letterbox(original_img)
        """
        self.new_shape = new_shape
        self.auto = auto
        self.scaleFill = scaleFill
        self.scaleup = scaleup
        self.stride = stride
        self.center = center  # Put the image in the middle or top-left

    def __call__(self, labels=None, image=None):
        """
        Resizes and pads an image for object detection, instance segmentation, or pose estimation tasks.

        This method applies letterboxing to the input image, which involves resizing the image while maintaining its
        aspect ratio and adding padding to fit the new shape. It also updates any associated labels accordingly.

        Args:
            labels (Dict | None): A dictionary containing image data and associated labels, or empty dict if None.
            image (np.ndarray | None): The input image as a numpy array. If None, the image is taken from 'labels'.

        Returns:
            (Dict | Tuple): If 'labels' is provided, returns an updated dictionary with the resized and padded image,
                updated labels, and additional metadata. If 'labels' is empty, returns a tuple containing the resized
                and padded image, and a tuple of (ratio, (left_pad, top_pad)).

        Examples:
            >>> letterbox = LetterBox(new_shape=(640, 640))
            >>> result = letterbox(labels={"img": np.zeros((480, 640, 3)), "instances": Instances(...)})
            >>> resized_img = result["img"]
            >>> updated_instances = result["instances"]
        """
        if labels is None:
            labels = {}
        img = labels.get("img") if image is None else image
        shape = img.shape[:2]  # current shape [height, width]
        new_shape = labels.pop("rect_shape", self.new_shape)
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        if not self.scaleup:  # only scale down, do not scale up (for better val mAP)
            r = min(r, 1.0)

        # Compute padding
        ratio = r, r  # width, height ratios
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
        if self.auto:  # minimum rectangle
            dw, dh = np.mod(dw, self.stride), np.mod(dh, self.stride)  # wh padding
        elif self.scaleFill:  # stretch
            dw, dh = 0.0, 0.0
            new_unpad = (new_shape[1], new_shape[0])
            ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]  # width, height ratios

        if self.center:
            dw /= 2  # divide padding into 2 sides
            dh /= 2

        if shape[::-1] != new_unpad:  # resize
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)) if self.center else 0, int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)) if self.center else 0, int(round(dw + 0.1))
        img = cv2.copyMakeBorder(
            img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )  # add border
        if labels.get("ratio_pad"):
            labels["ratio_pad"] = (labels["ratio_pad"], (left, top))  # for evaluation

        if len(labels):
            labels = self._update_labels(labels, ratio, left, top)
            labels["img"] = img
            labels["resized_shape"] = new_shape
            return labels
        else:
            return img

    @staticmethod
    def _update_labels(labels, ratio, padw, padh):
        """
        Updates labels after applying letterboxing to an image.

        This method modifies the bounding box coordinates of instances in the labels
        to account for resizing and padding applied during letterboxing.

        Args:
            labels (Dict): A dictionary containing image labels and instances.
            ratio (Tuple[float, float]): Scaling ratios (width, height) applied to the image.
            padw (float): Padding width added to the image.
            padh (float): Padding height added to the image.

        Returns:
            (Dict): Updated labels dictionary with modified instance coordinates.

        Examples:
            >>> letterbox = LetterBox(new_shape=(640, 640))
            >>> labels = {"instances": Instances(...)}
            >>> ratio = (0.5, 0.5)
            >>> padw, padh = 10, 20
            >>> updated_labels = letterbox._update_labels(labels, ratio, padw, padh)
        """
        labels["instances"].convert_bbox(format="xyxy")
        labels["instances"].denormalize(*labels["img"].shape[:2][::-1])
        labels["instances"].scale(*ratio)
        labels["instances"].add_padding(padw, padh)
        return labels


def pre_transform(im, imgsz=[1024, 1024], auto=True, stride=32):
        """
        Pre-transform input image before inference.

        Args:
            im (List(np.ndarray)): (N, 3, h, w) for tensor, [(h, w, 3) x N] for list.

        Returns:
            (list): A list of transformed images.
        """
        same_shapes = len({x.shape for x in im}) == 1
        letterbox = LetterBox(
            imgsz,
            auto=auto,
            stride=stride,
        )
        return [letterbox(image=x) for x in im]









def scale_boxes(img1_shape, boxes, img0_shape, ratio_pad=None, padding=True, xywh=False):
    """
    Rescales bounding boxes (in the format of xyxy by default) from the shape of the image they were originally
    specified in (img1_shape) to the shape of a different image (img0_shape).

    Args:
        img1_shape (tuple): The shape of the image that the bounding boxes are for, in the format of (height, width).
        boxes (torch.Tensor): the bounding boxes of the objects in the image, in the format of (x1, y1, x2, y2)
        img0_shape (tuple): the shape of the target image, in the format of (height, width).
        ratio_pad (tuple): a tuple of (ratio, pad) for scaling the boxes. If not provided, the ratio and pad will be
            calculated based on the size difference between the two images.
        padding (bool): If True, assuming the boxes is based on image augmented by yolo style. If False then do regular
            rescaling.
        xywh (bool): The box format is xywh or not, default=False.

    Returns:
        boxes (torch.Tensor): The scaled bounding boxes, in the format of (x1, y1, x2, y2)
    """
    if ratio_pad is None:  # calculate from img0_shape
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
        pad = (
            round((img1_shape[1] - img0_shape[1] * gain) / 2 - 0.1),
            round((img1_shape[0] - img0_shape[0] * gain) / 2 - 0.1),
        )  # wh padding
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]

    if padding:
        boxes[..., 0] -= pad[0]  # x padding
        boxes[..., 1] -= pad[1]  # y padding
        if not xywh:
            boxes[..., 2] -= pad[0]  # x padding
            boxes[..., 3] -= pad[1]  # y padding
    boxes[..., :4] /= gain
    return clip_boxes(boxes, img0_shape)


def crop_mask(masks, boxes):
    """
    It takes a mask and a bounding box, and returns a mask that is cropped to the bounding box.

    Args:
        masks (torch.Tensor): [n, h, w] tensor of masks
        boxes (torch.Tensor): [n, 4] tensor of bbox coordinates in relative point form

    Returns:
        (torch.Tensor): The masks are being cropped to the bounding box.
    """
    _, h, w = masks.shape
    x1, y1, x2, y2 = torch.chunk(boxes[:, :, None], 4, 1)  # x1 shape(n,1,1)
    r = torch.arange(w, device=masks.device, dtype=x1.dtype)[None, None, :]  # rows shape(1,1,w)
    c = torch.arange(h, device=masks.device, dtype=x1.dtype)[None, :, None]  # cols shape(1,h,1)

    return masks * ((r >= x1) * (r < x2) * (c >= y1) * (c < y2))


def process_mask(protos, masks_in, bboxes, shape, upsample=False):
    """
    Apply masks to bounding boxes using the output of the mask head.

    Args:
        protos (torch.Tensor): A tensor of shape [mask_dim, mask_h, mask_w].
        masks_in (torch.Tensor): A tensor of shape [n, mask_dim], where n is the number of masks after NMS.
        bboxes (torch.Tensor): A tensor of shape [n, 4], where n is the number of masks after NMS.
        shape (tuple): A tuple of integers representing the size of the input image in the format (h, w).
        upsample (bool): A flag to indicate whether to upsample the mask to the original image size. Default is False.

    Returns:
        (torch.Tensor): A binary mask tensor of shape [n, h, w], where n is the number of masks after NMS, and h and w
            are the height and width of the input image. The mask is applied to the bounding boxes.
    """
    c, mh, mw = protos.shape  # CHW
    ih, iw = shape
    masks = (masks_in @ protos.float().view(c, -1)).view(-1, mh, mw)  # CHW
    width_ratio = mw / iw
    height_ratio = mh / ih

    downsampled_bboxes = bboxes.clone()
    downsampled_bboxes[:, 0] *= width_ratio
    downsampled_bboxes[:, 2] *= width_ratio
    downsampled_bboxes[:, 3] *= height_ratio
    downsampled_bboxes[:, 1] *= height_ratio

    masks = crop_mask(masks, downsampled_bboxes)  # CHW
    if upsample:
        masks = F.interpolate(masks[None], shape, mode="bilinear", align_corners=False)[0]  # CHW
    return masks.gt_(0.0)


def _get_covariance_matrix(boxes):
    """
    Generating covariance matrix from obbs.

    Args:
        boxes (torch.Tensor): A tensor of shape (N, 5) representing rotated bounding boxes, with xywhr format.

    Returns:
        (torch.Tensor): Covariance matrices corresponding to original rotated bounding boxes.
    """
    # Gaussian bounding boxes, ignore the center points (the first two columns) because they are not needed here.
    gbbs = torch.cat((boxes[:, 2:4].pow(2) / 12, boxes[:, 4:]), dim=-1)
    a, b, c = gbbs.split(1, dim=-1)
    cos = c.cos()
    sin = c.sin()
    cos2 = cos.pow(2)
    sin2 = sin.pow(2)
    return a * cos2 + b * sin2, a * sin2 + b * cos2, (a - b) * cos * sin


def batch_probiou(obb1, obb2, eps=1e-7):
    """
    Calculate the prob IoU between oriented bounding boxes, https://arxiv.org/pdf/2106.06072v1.pdf.

    Args:
        obb1 (torch.Tensor | np.ndarray): A tensor of shape (N, 5) representing ground truth obbs, with xywhr format.
        obb2 (torch.Tensor | np.ndarray): A tensor of shape (M, 5) representing predicted obbs, with xywhr format.
        eps (float, optional): A small value to avoid division by zero. Defaults to 1e-7.

    Returns:
        (torch.Tensor): A tensor of shape (N, M) representing obb similarities.
    """
    obb1 = torch.from_numpy(obb1) if isinstance(obb1, np.ndarray) else obb1
    obb2 = torch.from_numpy(obb2) if isinstance(obb2, np.ndarray) else obb2

    x1, y1 = obb1[..., :2].split(1, dim=-1)
    x2, y2 = (x.squeeze(-1)[None] for x in obb2[..., :2].split(1, dim=-1))
    a1, b1, c1 = _get_covariance_matrix(obb1)
    a2, b2, c2 = (x.squeeze(-1)[None] for x in _get_covariance_matrix(obb2))

    t1 = (
        ((a1 + a2) * (y1 - y2).pow(2) + (b1 + b2) * (x1 - x2).pow(2)) / ((a1 + a2) * (b1 + b2) - (c1 + c2).pow(2) + eps)
    ) * 0.25
    t2 = (((c1 + c2) * (x2 - x1) * (y1 - y2)) / ((a1 + a2) * (b1 + b2) - (c1 + c2).pow(2) + eps)) * 0.5
    t3 = (
        ((a1 + a2) * (b1 + b2) - (c1 + c2).pow(2))
        / (4 * ((a1 * b1 - c1.pow(2)).clamp_(0) * (a2 * b2 - c2.pow(2)).clamp_(0)).sqrt() + eps)
        + eps
    ).log() * 0.5
    bd = (t1 + t2 + t3).clamp(eps, 100.0)
    hd = (1.0 - (-bd).exp() + eps).sqrt()
    return 1 - hd


def nms_rotated(boxes, scores, threshold=0.45, use_triu=True):
    """
    NMS for oriented bounding boxes using probiou and fast-nms.

    Args:
        boxes (torch.Tensor): Rotated bounding boxes, shape (N, 5), format xywhr.
        scores (torch.Tensor): Confidence scores, shape (N,).
        threshold (float, optional): IoU threshold. Defaults to 0.45.
        use_triu (bool, optional): Whether to use `torch.triu` operator. It'd be useful for disable it
            when exporting obb models to some formats that do not support `torch.triu`.

    Returns:
        (torch.Tensor): Indices of boxes to keep after NMS.
    """
    sorted_idx = torch.argsort(scores, descending=True)
    boxes = boxes[sorted_idx]
    ious = batch_probiou(boxes, boxes)
    if use_triu:
        ious = ious.triu_(diagonal=1)
        # pick = torch.nonzero(ious.max(dim=0)[0] < threshold).squeeze_(-1)
        # NOTE: handle the case when len(boxes) hence exportable by eliminating if-else condition
        pick = torch.nonzero((ious >= threshold).sum(0) <= 0).squeeze_(-1)
    else:
        n = boxes.shape[0]
        row_idx = torch.arange(n, device=boxes.device).view(-1, 1).expand(-1, n)
        col_idx = torch.arange(n, device=boxes.device).view(1, -1).expand(n, -1)
        upper_mask = row_idx < col_idx
        ious = ious * upper_mask
        # Zeroing these scores ensures the additional indices would not affect the final results
        scores[~((ious >= threshold).sum(0) <= 0)] = 0
        # NOTE: return indices with fixed length to avoid TFLite reshape error
        pick = torch.topk(scores, scores.shape[0]).indices
    return sorted_idx[pick]


def xywh2xyxy(x):
    """
    Convert bounding box coordinates from (x, y, width, height) format to (x1, y1, x2, y2) format where (x1, y1) is the
    top-left corner and (x2, y2) is the bottom-right corner. Note: ops per 2 channels faster than per channel.

    Args:
        x (np.ndarray | torch.Tensor): The input bounding box coordinates in (x, y, width, height) format.

    Returns:
        y (np.ndarray | torch.Tensor): The bounding box coordinates in (x1, y1, x2, y2) format.
    """
    assert x.shape[-1] == 4, f"input shape last dimension expected 4 but input shape is {x.shape}"
    y = empty_like(x)  # faster than clone/copy
    xy = x[..., :2]  # centers
    wh = x[..., 2:] / 2  # half width-height
    y[..., :2] = xy - wh  # top left xy
    y[..., 2:] = xy + wh  # bottom right xy
    return y

def non_max_suppression(
    prediction,
    conf_thres=0.25,
    iou_thres=0.45,
    classes=None,
    agnostic=False,
    multi_label=False,
    labels=(),
    max_det=300,
    nc=0,  # number of classes (optional)
    max_time_img=0.05,
    max_nms=30000,
    max_wh=7680,
    in_place=True,
    rotated=False,
    end2end=False,
):
    """
    Perform non-maximum suppression (NMS) on a set of boxes, with support for masks and multiple labels per box.

    Args:
        prediction (torch.Tensor): A tensor of shape (batch_size, num_classes + 4 + num_masks, num_boxes)
            containing the predicted boxes, classes, and masks. The tensor should be in the format
            output by a model, such as YOLO.
        conf_thres (float): The confidence threshold below which boxes will be filtered out.
            Valid values are between 0.0 and 1.0.
        iou_thres (float): The IoU threshold below which boxes will be filtered out during NMS.
            Valid values are between 0.0 and 1.0.
        classes (List[int]): A list of class indices to consider. If None, all classes will be considered.
        agnostic (bool): If True, the model is agnostic to the number of classes, and all
            classes will be considered as one.
        multi_label (bool): If True, each box may have multiple labels.
        labels (List[List[Union[int, float, torch.Tensor]]]): A list of lists, where each inner
            list contains the apriori labels for a given image. The list should be in the format
            output by a dataloader, with each label being a tuple of (class_index, x1, y1, x2, y2).
        max_det (int): The maximum number of boxes to keep after NMS.
        nc (int, optional): The number of classes output by the model. Any indices after this will be considered masks.
        max_time_img (float): The maximum time (seconds) for processing one image.
        max_nms (int): The maximum number of boxes into torchvision.ops.nms().
        max_wh (int): The maximum box width and height in pixels.
        in_place (bool): If True, the input prediction tensor will be modified in place.
        rotated (bool): If Oriented Bounding Boxes (OBB) are being passed for NMS.
        end2end (bool): If the model doesn't require NMS.

    Returns:
        (List[torch.Tensor]): A list of length batch_size, where each element is a tensor of
            shape (num_boxes, 6 + num_masks) containing the kept boxes, with columns
            (x1, y1, x2, y2, confidence, class, mask1, mask2, ...).
    """
    import torchvision  # scope for faster 'import ultralytics'

    # Checks
    assert 0 <= conf_thres <= 1, f"Invalid Confidence threshold {conf_thres}, valid values are between 0.0 and 1.0"
    assert 0 <= iou_thres <= 1, f"Invalid IoU {iou_thres}, valid values are between 0.0 and 1.0"
    if isinstance(prediction, (list, tuple)):  # YOLOv8 model in validation model, output = (inference_out, loss_out)
        prediction = prediction[0]  # select only inference output
    if classes is not None:
        classes = torch.tensor(classes, device=prediction.device)

    if prediction.shape[-1] == 6 or end2end:  # end-to-end model (BNC, i.e. 1,300,6)
        output = [pred[pred[:, 4] > conf_thres][:max_det] for pred in prediction]
        if classes is not None:
            output = [pred[(pred[:, 5:6] == classes).any(1)] for pred in output]
        return output

    bs = prediction.shape[0]  # batch size (BCN, i.e. 1,84,6300)
    nc = nc or (prediction.shape[1] - 4)  # number of classes
    nm = prediction.shape[1] - nc - 4  # number of masks
    mi = 4 + nc  # mask start index
    xc = prediction[:, 4:mi].amax(1) > conf_thres  # candidates

    # Settings
    # min_wh = 2  # (pixels) minimum box width and height
    time_limit = 2.0 + max_time_img * bs  # seconds to quit after
    multi_label &= nc > 1  # multiple labels per box (adds 0.5ms/img)

    prediction = prediction.transpose(-1, -2)  # shape(1,84,6300) to shape(1,6300,84)
    if not rotated:
        if in_place:
            prediction[..., :4] = xywh2xyxy(prediction[..., :4])  # xywh to xyxy
        else:
            prediction = torch.cat((xywh2xyxy(prediction[..., :4]), prediction[..., 4:]), dim=-1)  # xywh to xyxy

    t = time.time()
    output = [torch.zeros((0, 6 + nm), device=prediction.device)] * bs
    for xi, x in enumerate(prediction):  # image index, image inference
        # Apply constraints
        # x[((x[:, 2:4] < min_wh) | (x[:, 2:4] > max_wh)).any(1), 4] = 0  # width-height
        x = x[xc[xi]]  # confidence

        # Cat apriori labels if autolabelling
        if labels and len(labels[xi]) and not rotated:
            lb = labels[xi]
            v = torch.zeros((len(lb), nc + nm + 4), device=x.device)
            v[:, :4] = xywh2xyxy(lb[:, 1:5])  # box
            v[range(len(lb)), lb[:, 0].long() + 4] = 1.0  # cls
            x = torch.cat((x, v), 0)

        # If none remain process next image
        if not x.shape[0]:
            continue

        # Detections matrix nx6 (xyxy, conf, cls)
        box, cls, mask = x.split((4, nc, nm), 1)

        if multi_label:
            i, j = torch.where(cls > conf_thres)
            x = torch.cat((box[i], x[i, 4 + j, None], j[:, None].float(), mask[i]), 1)
        else:  # best class only
            conf, j = cls.max(1, keepdim=True)
            x = torch.cat((box, conf, j.float(), mask), 1)[conf.view(-1) > conf_thres]

        # Filter by class
        if classes is not None:
            x = x[(x[:, 5:6] == classes).any(1)]

        # Check shape
        n = x.shape[0]  # number of boxes
        if not n:  # no boxes
            continue
        if n > max_nms:  # excess boxes
            x = x[x[:, 4].argsort(descending=True)[:max_nms]]  # sort by confidence and remove excess boxes

        # Batched NMS
        c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
        scores = x[:, 4]  # scores
        if rotated:
            boxes = torch.cat((x[:, :2] + c, x[:, 2:4], x[:, -1:]), dim=-1)  # xywhr
            i = nms_rotated(boxes, scores, iou_thres)
        else:
            boxes = x[:, :4] + c  # boxes (offset by class)
            i = torchvision.ops.nms(boxes, scores, iou_thres)  # NMS
        i = i[:max_det]  # limit detections

        # # Experimental
        # merge = False  # use merge-NMS
        # if merge and (1 < n < 3E3):  # Merge NMS (boxes merged using weighted mean)
        #     # Update boxes as boxes(i,4) = weights(i,n) * boxes(n,4)
        #     from .metrics import box_iou
        #     iou = box_iou(boxes[i], boxes) > iou_thres  # IoU matrix
        #     weights = iou * scores[None]  # box weights
        #     x[i, :4] = torch.mm(weights, x[:, :4]).float() / weights.sum(1, keepdim=True)  # merged boxes
        #     redundant = True  # require redundant detections
        #     if redundant:
        #         i = i[iou.sum(1) > 1]  # require redundancy

        output[xi] = x[i]
        if (time.time() - t) > time_limit:
            print(f"WARNING ⚠️ NMS time limit {time_limit:.3f}s exceeded")
            break  # time limit exceeded

    return output




def clip_coords(coords, shape):
    """
    Clip line coordinates to the image boundaries.

    Args:
        coords (torch.Tensor | numpy.ndarray): A list of line coordinates.
        shape (tuple): A tuple of integers representing the size of the image in the format (height, width).

    Returns:
        (torch.Tensor | numpy.ndarray): Clipped coordinates
    """
    if isinstance(coords, torch.Tensor):  # faster individually (WARNING: inplace .clamp_() Apple MPS bug)
        coords[..., 0] = coords[..., 0].clamp(0, shape[1])  # x
        coords[..., 1] = coords[..., 1].clamp(0, shape[0])  # y
    else:  # np.array (faster grouped)
        coords[..., 0] = coords[..., 0].clip(0, shape[1])  # x
        coords[..., 1] = coords[..., 1].clip(0, shape[0])  # y
    return coords


def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None, normalize=False, padding=True):
    """
    Rescale segment coordinates (xy) from img1_shape to img0_shape.

    Args:
        img1_shape (tuple): The shape of the image that the coords are from.
        coords (torch.Tensor): the coords to be scaled of shape n,2.
        img0_shape (tuple): the shape of the image that the segmentation is being applied to.
        ratio_pad (tuple): the ratio of the image size to the padded image size.
        normalize (bool): If True, the coordinates will be normalized to the range [0, 1]. Defaults to False.
        padding (bool): If True, assuming the boxes is based on image augmented by yolo style. If False then do regular
            rescaling.

    Returns:
        coords (torch.Tensor): The scaled coordinates.
    """
    if ratio_pad is None:  # calculate from img0_shape
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
        pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]

    if padding:
        coords[..., 0] -= pad[0]  # x padding
        coords[..., 1] -= pad[1]  # y padding
    coords[..., 0] /= gain
    coords[..., 1] /= gain
    coords = clip_coords(coords, img0_shape)
    if normalize:
        coords[..., 0] /= img0_shape[1]  # width
        coords[..., 1] /= img0_shape[0]  # height
    return coords


def empty_like(x):
    """Creates empty torch.Tensor or np.ndarray with same shape as input and float32 dtype."""
    return (
        torch.empty_like(x, dtype=torch.float32) if isinstance(x, torch.Tensor) else np.empty_like(x, dtype=np.float32)
    )


def xyxy2xywh(x):
    """
    Convert bounding box coordinates from (x1, y1, x2, y2) format to (x, y, width, height) format where (x1, y1) is the
    top-left corner and (x2, y2) is the bottom-right corner.

    Args:
        x (np.ndarray | torch.Tensor): The input bounding box coordinates in (x1, y1, x2, y2) format.

    Returns:
        y (np.ndarray | torch.Tensor): The bounding box coordinates in (x, y, width, height) format.
    """
    assert x.shape[-1] == 4, f"input shape last dimension expected 4 but input shape is {x.shape}"
    y = empty_like(x)  # faster than clone/copy
    y[..., 0] = (x[..., 0] + x[..., 2]) / 2  # x center
    y[..., 1] = (x[..., 1] + x[..., 3]) / 2  # y center
    y[..., 2] = x[..., 2] - x[..., 0]  # width
    y[..., 3] = x[..., 3] - x[..., 1]  # height
    return y



class SimpleClass:
    """
    A simple base class for creating objects with string representations of their attributes.

    This class provides a foundation for creating objects that can be easily printed or represented as strings,
    showing all their non-callable attributes. It's useful for debugging and introspection of object states.

    Methods:
        __str__: Returns a human-readable string representation of the object.
        __repr__: Returns a machine-readable string representation of the object.
        __getattr__: Provides a custom attribute access error message with helpful information.

    Examples:
        >>> class MyClass(SimpleClass):
        ...     def __init__(self):
        ...         self.x = 10
        ...         self.y = "hello"
        >>> obj = MyClass()
        >>> print(obj)
        __main__.MyClass object with attributes:

        x: 10
        y: 'hello'

    Notes:
        - This class is designed to be subclassed. It provides a convenient way to inspect object attributes.
        - The string representation includes the module and class name of the object.
        - Callable attributes and attributes starting with an underscore are excluded from the string representation.
    """

    def __str__(self):
        """Return a human-readable string representation of the object."""
        attr = []
        for a in dir(self):
            v = getattr(self, a)
            if not callable(v) and not a.startswith("_"):
                if isinstance(v, SimpleClass):
                    # Display only the module and class name for subclasses
                    s = f"{a}: {v.__module__}.{v.__class__.__name__} object"
                else:
                    s = f"{a}: {repr(v)}"
                attr.append(s)
        return f"{self.__module__}.{self.__class__.__name__} object with attributes:\n\n" + "\n".join(attr)

    def __repr__(self):
        """Return a machine-readable string representation of the object."""
        return self.__str__()

    def __getattr__(self, attr):
        """Custom attribute access error message with helpful information."""
        name = self.__class__.__name__
        raise AttributeError(f"'{name}' object has no attribute '{attr}'. See valid attributes below.\n{self.__doc__}")



class BaseTensor(SimpleClass):
    """
    Base tensor class with additional methods for easy manipulation and device handling.

    Attributes:
        data (torch.Tensor | np.ndarray): Prediction data such as bounding boxes, masks, or keypoints.
        orig_shape (Tuple[int, int]): Original shape of the image, typically in the format (height, width).

    Methods:
        cpu: Return a copy of the tensor stored in CPU memory.
        numpy: Returns a copy of the tensor as a numpy array.
        cuda: Moves the tensor to GPU memory, returning a new instance if necessary.
        to: Return a copy of the tensor with the specified device and dtype.

    Examples:
        >>> import torch
        >>> data = torch.tensor([[1, 2, 3], [4, 5, 6]])
        >>> orig_shape = (720, 1280)
        >>> base_tensor = BaseTensor(data, orig_shape)
        >>> cpu_tensor = base_tensor.cpu()
        >>> numpy_array = base_tensor.numpy()
        >>> gpu_tensor = base_tensor.cuda()
    """

    def __init__(self, data, orig_shape) -> None:
        """
        Initialize BaseTensor with prediction data and the original shape of the image.

        Args:
            data (torch.Tensor | np.ndarray): Prediction data such as bounding boxes, masks, or keypoints.
            orig_shape (Tuple[int, int]): Original shape of the image in (height, width) format.

        Examples:
            >>> import torch
            >>> data = torch.tensor([[1, 2, 3], [4, 5, 6]])
            >>> orig_shape = (720, 1280)
            >>> base_tensor = BaseTensor(data, orig_shape)
        """
        assert isinstance(data, (torch.Tensor, np.ndarray)), "data must be torch.Tensor or np.ndarray"
        self.data = data
        self.orig_shape = orig_shape

    @property
    def shape(self):
        """
        Returns the shape of the underlying data tensor.

        Returns:
            (Tuple[int, ...]): The shape of the data tensor.

        Examples:
            >>> data = torch.rand(100, 4)
            >>> base_tensor = BaseTensor(data, orig_shape=(720, 1280))
            >>> print(base_tensor.shape)
            (100, 4)
        """
        return self.data.shape

    def cpu(self):
        """
        Returns a copy of the tensor stored in CPU memory.

        Returns:
            (BaseTensor): A new BaseTensor object with the data tensor moved to CPU memory.

        Examples:
            >>> data = torch.tensor([[1, 2, 3], [4, 5, 6]]).cuda()
            >>> base_tensor = BaseTensor(data, orig_shape=(720, 1280))
            >>> cpu_tensor = base_tensor.cpu()
            >>> isinstance(cpu_tensor, BaseTensor)
            True
            >>> cpu_tensor.data.device
            device(type='cpu')
        """
        return self if isinstance(self.data, np.ndarray) else self.__class__(self.data.cpu(), self.orig_shape)

    def numpy(self):
        """
        Returns a copy of the tensor as a numpy array.

        Returns:
            (np.ndarray): A numpy array containing the same data as the original tensor.

        Examples:
            >>> data = torch.tensor([[1, 2, 3], [4, 5, 6]])
            >>> orig_shape = (720, 1280)
            >>> base_tensor = BaseTensor(data, orig_shape)
            >>> numpy_array = base_tensor.numpy()
            >>> print(type(numpy_array))
            <class 'numpy.ndarray'>
        """
        return self if isinstance(self.data, np.ndarray) else self.__class__(self.data.numpy(), self.orig_shape)

    def cuda(self):
        """
        Moves the tensor to GPU memory.

        Returns:
            (BaseTensor): A new BaseTensor instance with the data moved to GPU memory if it's not already a
                numpy array, otherwise returns self.

        Examples:
            >>> import torch
            >>> from ultralytics.engine.results import BaseTensor
            >>> data = torch.tensor([[1, 2, 3], [4, 5, 6]])
            >>> base_tensor = BaseTensor(data, orig_shape=(720, 1280))
            >>> gpu_tensor = base_tensor.cuda()
            >>> print(gpu_tensor.data.device)
            cuda:0
        """
        return self.__class__(torch.as_tensor(self.data).cuda(), self.orig_shape)

    def to(self, *args, **kwargs):
        """
        Return a copy of the tensor with the specified device and dtype.

        Args:
            *args (Any): Variable length argument list to be passed to torch.Tensor.to().
            **kwargs (Any): Arbitrary keyword arguments to be passed to torch.Tensor.to().

        Returns:
            (BaseTensor): A new BaseTensor instance with the data moved to the specified device and/or dtype.

        Examples:
            >>> base_tensor = BaseTensor(torch.randn(3, 4), orig_shape=(480, 640))
            >>> cuda_tensor = base_tensor.to("cuda")
            >>> float16_tensor = base_tensor.to(dtype=torch.float16)
        """
        return self.__class__(torch.as_tensor(self.data).to(*args, **kwargs), self.orig_shape)

    def __len__(self):  # override len(results)
        """
        Returns the length of the underlying data tensor.

        Returns:
            (int): The number of elements in the first dimension of the data tensor.

        Examples:
            >>> data = torch.tensor([[1, 2, 3], [4, 5, 6]])
            >>> base_tensor = BaseTensor(data, orig_shape=(720, 1280))
            >>> len(base_tensor)
            2
        """
        return len(self.data)

    def __getitem__(self, idx):
        """
        Returns a new BaseTensor instance containing the specified indexed elements of the data tensor.

        Args:
            idx (int | List[int] | torch.Tensor): Index or indices to select from the data tensor.

        Returns:
            (BaseTensor): A new BaseTensor instance containing the indexed data.

        Examples:
            >>> data = torch.tensor([[1, 2, 3], [4, 5, 6]])
            >>> base_tensor = BaseTensor(data, orig_shape=(720, 1280))
            >>> result = base_tensor[0]  # Select the first row
            >>> print(result.data)
            tensor([1, 2, 3])
        """
        return self.__class__(self.data[idx], self.orig_shape)


class Probs(BaseTensor):
    """
    A class for storing and manipulating classification probabilities.

    This class extends BaseTensor and provides methods for accessing and manipulating
    classification probabilities, including top-1 and top-5 predictions.

    Attributes:
        data (torch.Tensor | numpy.ndarray): The raw tensor or array containing classification probabilities.
        orig_shape (tuple | None): The original image shape as (height, width). Not used in this class.
        top1 (int): Index of the class with the highest probability.
        top5 (List[int]): Indices of the top 5 classes by probability.
        top1conf (torch.Tensor | numpy.ndarray): Confidence score of the top 1 class.
        top5conf (torch.Tensor | numpy.ndarray): Confidence scores of the top 5 classes.

    Methods:
        cpu(): Returns a copy of the probabilities tensor on CPU memory.
        numpy(): Returns a copy of the probabilities tensor as a numpy array.
        cuda(): Returns a copy of the probabilities tensor on GPU memory.
        to(*args, **kwargs): Returns a copy of the probabilities tensor with specified device and dtype.

    Examples:
        >>> probs = torch.tensor([0.1, 0.3, 0.6])
        >>> p = Probs(probs)
        >>> print(p.top1)
        2
        >>> print(p.top5)
        [2, 1, 0]
        >>> print(p.top1conf)
        tensor(0.6000)
        >>> print(p.top5conf)
        tensor([0.6000, 0.3000, 0.1000])
    """

    def __init__(self, probs, orig_shape=None) -> None:
        """
        Initialize the Probs class with classification probabilities.

        This class stores and manages classification probabilities, providing easy access to top predictions and their
        confidences.

        Args:
            probs (torch.Tensor | np.ndarray): A 1D tensor or array of classification probabilities.
            orig_shape (tuple | None): The original image shape as (height, width). Not used in this class but kept for
                consistency with other result classes.

        Attributes:
            data (torch.Tensor | np.ndarray): The raw tensor or array containing classification probabilities.
            top1 (int): Index of the top 1 class.
            top5 (List[int]): Indices of the top 5 classes.
            top1conf (torch.Tensor | np.ndarray): Confidence of the top 1 class.
            top5conf (torch.Tensor | np.ndarray): Confidences of the top 5 classes.

        Examples:
            >>> import torch
            >>> probs = torch.tensor([0.1, 0.3, 0.2, 0.4])
            >>> p = Probs(probs)
            >>> print(p.top1)
            3
            >>> print(p.top1conf)
            tensor(0.4000)
            >>> print(p.top5)
            [3, 1, 2, 0]
        """
        super().__init__(probs, orig_shape)

    @property
    @lru_cache(maxsize=1)
    def top1(self):
        """
        Returns the index of the class with the highest probability.

        Returns:
            (int): Index of the class with the highest probability.

        Examples:
            >>> probs = Probs(torch.tensor([0.1, 0.3, 0.6]))
            >>> probs.top1
            2
        """
        return int(self.data.argmax())

    @property
    @lru_cache(maxsize=1)
    def top5(self):
        """
        Returns the indices of the top 5 class probabilities.

        Returns:
            (List[int]): A list containing the indices of the top 5 class probabilities, sorted in descending order.

        Examples:
            >>> probs = Probs(torch.tensor([0.1, 0.2, 0.3, 0.4, 0.5]))
            >>> print(probs.top5)
            [4, 3, 2, 1, 0]
        """
        return (-self.data).argsort(0)[:5].tolist()  # this way works with both torch and numpy.

    @property
    @lru_cache(maxsize=1)
    def top1conf(self):
        """
        Returns the confidence score of the highest probability class.

        This property retrieves the confidence score (probability) of the class with the highest predicted probability
        from the classification results.

        Returns:
            (torch.Tensor | numpy.ndarray): A tensor containing the confidence score of the top 1 class.

        Examples:
            >>> results = model("image.jpg")  # classify an image
            >>> probs = results[0].probs  # get classification probabilities
            >>> top1_confidence = probs.top1conf  # get confidence of top 1 class
            >>> print(f"Top 1 class confidence: {top1_confidence.item():.4f}")
        """
        return self.data[self.top1]

    @property
    @lru_cache(maxsize=1)
    def top5conf(self):
        """
        Returns confidence scores for the top 5 classification predictions.

        This property retrieves the confidence scores corresponding to the top 5 class probabilities
        predicted by the model. It provides a quick way to access the most likely class predictions
        along with their associated confidence levels.

        Returns:
            (torch.Tensor | numpy.ndarray): A tensor or array containing the confidence scores for the
                top 5 predicted classes, sorted in descending order of probability.

        Examples:
            >>> results = model("image.jpg")
            >>> probs = results[0].probs
            >>> top5_conf = probs.top5conf
            >>> print(top5_conf)  # Prints confidence scores for top 5 classes
        """
        return self.data[self.top5]



class Boxes(BaseTensor):
    """
    A class for managing and manipulating detection boxes.

    This class provides functionality for handling detection boxes, including their coordinates, confidence scores,
    class labels, and optional tracking IDs. It supports various box formats and offers methods for easy manipulation
    and conversion between different coordinate systems.

    Attributes:
        data (torch.Tensor | numpy.ndarray): The raw tensor containing detection boxes and associated data.
        orig_shape (Tuple[int, int]): The original image dimensions (height, width).
        is_track (bool): Indicates whether tracking IDs are included in the box data.
        xyxy (torch.Tensor | numpy.ndarray): Boxes in [x1, y1, x2, y2] format.
        conf (torch.Tensor | numpy.ndarray): Confidence scores for each box.
        cls (torch.Tensor | numpy.ndarray): Class labels for each box.
        id (torch.Tensor | numpy.ndarray): Tracking IDs for each box (if available).
        xywh (torch.Tensor | numpy.ndarray): Boxes in [x, y, width, height] format.
        xyxyn (torch.Tensor | numpy.ndarray): Normalized [x1, y1, x2, y2] boxes relative to orig_shape.
        xywhn (torch.Tensor | numpy.ndarray): Normalized [x, y, width, height] boxes relative to orig_shape.

    Methods:
        cpu(): Returns a copy of the object with all tensors on CPU memory.
        numpy(): Returns a copy of the object with all tensors as numpy arrays.
        cuda(): Returns a copy of the object with all tensors on GPU memory.
        to(*args, **kwargs): Returns a copy of the object with tensors on specified device and dtype.

    Examples:
        >>> import torch
        >>> boxes_data = torch.tensor([[100, 50, 150, 100, 0.9, 0], [200, 150, 300, 250, 0.8, 1]])
        >>> orig_shape = (480, 640)  # height, width
        >>> boxes = Boxes(boxes_data, orig_shape)
        >>> print(boxes.xyxy)
        >>> print(boxes.conf)
        >>> print(boxes.cls)
        >>> print(boxes.xywhn)
    """

    def __init__(self, boxes, orig_shape) -> None:
        """
        Initialize the Boxes class with detection box data and the original image shape.

        This class manages detection boxes, providing easy access and manipulation of box coordinates,
        confidence scores, class identifiers, and optional tracking IDs. It supports multiple formats
        for box coordinates, including both absolute and normalized forms.

        Args:
            boxes (torch.Tensor | np.ndarray): A tensor or numpy array with detection boxes of shape
                (num_boxes, 6) or (num_boxes, 7). Columns should contain
                [x1, y1, x2, y2, confidence, class, (optional) track_id].
            orig_shape (Tuple[int, int]): The original image shape as (height, width). Used for normalization.

        Attributes:
            data (torch.Tensor): The raw tensor containing detection boxes and their associated data.
            orig_shape (Tuple[int, int]): The original image size, used for normalization.
            is_track (bool): Indicates whether tracking IDs are included in the box data.

        Examples:
            >>> import torch
            >>> boxes = torch.tensor([[100, 50, 150, 100, 0.9, 0]])
            >>> orig_shape = (480, 640)
            >>> detection_boxes = Boxes(boxes, orig_shape)
            >>> print(detection_boxes.xyxy)
            tensor([[100.,  50., 150., 100.]])
        """
        if boxes.ndim == 1:
            boxes = boxes[None, :]
        n = boxes.shape[-1]
        assert n in {6, 7}, f"expected 6 or 7 values but got {n}"  # xyxy, track_id, conf, cls
        super().__init__(boxes, orig_shape)
        self.is_track = n == 7
        self.orig_shape = orig_shape

    @property
    def xyxy(self):
        """
        Returns bounding boxes in [x1, y1, x2, y2] format.

        Returns:
            (torch.Tensor | numpy.ndarray): A tensor or numpy array of shape (n, 4) containing bounding box
                coordinates in [x1, y1, x2, y2] format, where n is the number of boxes.

        Examples:
            >>> results = model("image.jpg")
            >>> boxes = results[0].boxes
            >>> xyxy = boxes.xyxy
            >>> print(xyxy)
        """
        return self.data[:, :4]

    @property
    def conf(self):
        """
        Returns the confidence scores for each detection box.

        Returns:
            (torch.Tensor | numpy.ndarray): A 1D tensor or array containing confidence scores for each detection,
                with shape (N,) where N is the number of detections.

        Examples:
            >>> boxes = Boxes(torch.tensor([[10, 20, 30, 40, 0.9, 0]]), orig_shape=(100, 100))
            >>> conf_scores = boxes.conf
            >>> print(conf_scores)
            tensor([0.9000])
        """
        return self.data[:, -2]

    @property
    def cls(self):
        """
        Returns the class ID tensor representing category predictions for each bounding box.

        Returns:
            (torch.Tensor | numpy.ndarray): A tensor or numpy array containing the class IDs for each detection box.
                The shape is (N,), where N is the number of boxes.

        Examples:
            >>> results = model("image.jpg")
            >>> boxes = results[0].boxes
            >>> class_ids = boxes.cls
            >>> print(class_ids)  # tensor([0., 2., 1.])
        """
        return self.data[:, -1]

    @property
    def id(self):
        """
        Returns the tracking IDs for each detection box if available.

        Returns:
            (torch.Tensor | None): A tensor containing tracking IDs for each box if tracking is enabled,
                otherwise None. Shape is (N,) where N is the number of boxes.

        Examples:
            >>> results = model.track("path/to/video.mp4")
            >>> for result in results:
            ...     boxes = result.boxes
            ...     if boxes.is_track:
            ...         track_ids = boxes.id
            ...         print(f"Tracking IDs: {track_ids}")
            ...     else:
            ...         print("Tracking is not enabled for these boxes.")

        Notes:
            - This property is only available when tracking is enabled (i.e., when `is_track` is True).
            - The tracking IDs are typically used to associate detections across multiple frames in video analysis.
        """
        return self.data[:, -3] if self.is_track else None

    @property
    @lru_cache(maxsize=2)  # maxsize 1 should suffice
    def xywh(self):
        """
        Convert bounding boxes from [x1, y1, x2, y2] format to [x, y, width, height] format.

        Returns:
            (torch.Tensor | numpy.ndarray): Boxes in [x_center, y_center, width, height] format, where x_center, y_center are the coordinates of
                the center point of the bounding box, width, height are the dimensions of the bounding box and the
                shape of the returned tensor is (N, 4), where N is the number of boxes.

        Examples:
            >>> boxes = Boxes(torch.tensor([[100, 50, 150, 100], [200, 150, 300, 250]]), orig_shape=(480, 640))
            >>> xywh = boxes.xywh
            >>> print(xywh)
            tensor([[100.0000,  50.0000,  50.0000,  50.0000],
                    [200.0000, 150.0000, 100.0000, 100.0000]])
        """
        return xyxy2xywh(self.xyxy)

    @property
    @lru_cache(maxsize=2)
    def xyxyn(self):
        """
        Returns normalized bounding box coordinates relative to the original image size.

        This property calculates and returns the bounding box coordinates in [x1, y1, x2, y2] format,
        normalized to the range [0, 1] based on the original image dimensions.

        Returns:
            (torch.Tensor | numpy.ndarray): Normalized bounding box coordinates with shape (N, 4), where N is
                the number of boxes. Each row contains [x1, y1, x2, y2] values normalized to [0, 1].

        Examples:
            >>> boxes = Boxes(torch.tensor([[100, 50, 300, 400, 0.9, 0]]), orig_shape=(480, 640))
            >>> normalized = boxes.xyxyn
            >>> print(normalized)
            tensor([[0.1562, 0.1042, 0.4688, 0.8333]])
        """
        xyxy = self.xyxy.clone() if isinstance(self.xyxy, torch.Tensor) else np.copy(self.xyxy)
        xyxy[..., [0, 2]] /= self.orig_shape[1]
        xyxy[..., [1, 3]] /= self.orig_shape[0]
        return xyxy

    @property
    @lru_cache(maxsize=2)
    def xywhn(self):
        """
        Returns normalized bounding boxes in [x, y, width, height] format.

        This property calculates and returns the normalized bounding box coordinates in the format
        [x_center, y_center, width, height], where all values are relative to the original image dimensions.

        Returns:
            (torch.Tensor | numpy.ndarray): Normalized bounding boxes with shape (N, 4), where N is the
                number of boxes. Each row contains [x_center, y_center, width, height] values normalized
                to [0, 1] based on the original image dimensions.

        Examples:
            >>> boxes = Boxes(torch.tensor([[100, 50, 150, 100, 0.9, 0]]), orig_shape=(480, 640))
            >>> normalized = boxes.xywhn
            >>> print(normalized)
            tensor([[0.1953, 0.1562, 0.0781, 0.1042]])
        """
        xywh = xyxy2xywh(self.xyxy)
        xywh[..., [0, 2]] /= self.orig_shape[1]
        xywh[..., [1, 3]] /= self.orig_shape[0]
        return xywh


def min_index(arr1, arr2):
    """
    Find a pair of indexes with the shortest distance between two arrays of 2D points.

    Args:
        arr1 (np.ndarray): A NumPy array of shape (N, 2) representing N 2D points.
        arr2 (np.ndarray): A NumPy array of shape (M, 2) representing M 2D points.

    Returns:
        (tuple): A tuple containing the indexes of the points with the shortest distance in arr1 and arr2 respectively.
    """
    dis = ((arr1[:, None, :] - arr2[None, :, :]) ** 2).sum(-1)
    return np.unravel_index(np.argmin(dis, axis=None), dis.shape)



def merge_multi_segment(segments):
    """
    Merge multiple segments into one list by connecting the coordinates with the minimum distance between each segment.
    This function connects these coordinates with a thin line to merge all segments into one.

    Args:
        segments (List[List]): Original segmentations in COCO's JSON file.
                               Each element is a list of coordinates, like [segmentation1, segmentation2,...].

    Returns:
        s (List[np.ndarray]): A list of connected segments represented as NumPy arrays.
    """
    s = []
    segments = [np.array(i).reshape(-1, 2) for i in segments]
    idx_list = [[] for _ in range(len(segments))]

    # Record the indexes with min distance between each segment
    for i in range(1, len(segments)):
        idx1, idx2 = min_index(segments[i - 1], segments[i])
        idx_list[i - 1].append(idx1)
        idx_list[i].append(idx2)

    # Use two round to connect all the segments
    for k in range(2):
        # Forward connection
        if k == 0:
            for i, idx in enumerate(idx_list):
                # Middle segments have two indexes, reverse the index of middle segments
                if len(idx) == 2 and idx[0] > idx[1]:
                    idx = idx[::-1]
                    segments[i] = segments[i][::-1, :]

                segments[i] = np.roll(segments[i], -idx[0], axis=0)
                segments[i] = np.concatenate([segments[i], segments[i][:1]])
                # Deal with the first segment and the last one
                if i in {0, len(idx_list) - 1}:
                    s.append(segments[i])
                else:
                    idx = [0, idx[1] - idx[0]]
                    s.append(segments[i][idx[0] : idx[1] + 1])

        else:
            for i in range(len(idx_list) - 1, -1, -1):
                if i not in {0, len(idx_list) - 1}:
                    idx = idx_list[i]
                    nidx = abs(idx[1] - idx[0])
                    s.append(segments[i][nidx:])
    return s


def masks2segments(masks, strategy="all"):
    """
    It takes a list of masks(n,h,w) and returns a list of segments(n,xy).

    Args:
        masks (torch.Tensor): the output of the model, which is a tensor of shape (batch_size, 160, 160)
        strategy (str): 'all' or 'largest'. Defaults to all

    Returns:
        segments (List): list of segment masks
    """


    segments = []
    for x in masks.int().cpu().numpy().astype("uint8"):
        c = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        if c:
            if strategy == "all":  # merge and concatenate all segments
                c = (
                    np.concatenate(merge_multi_segment([x.reshape(-1, 2) for x in c]))
                    if len(c) > 1
                    else c[0].reshape(-1, 2)
                )
            elif strategy == "largest":  # select largest segment
                c = np.array(c[np.array([len(x) for x in c]).argmax()]).reshape(-1, 2)
        else:
            c = np.zeros((0, 2))  # no segments found
        segments.append(c.astype("float32"))
    return segments


class Masks(BaseTensor):
    """
    A class for storing and manipulating detection masks.

    This class extends BaseTensor and provides functionality for handling segmentation masks,
    including methods for converting between pixel and normalized coordinates.

    Attributes:
        data (torch.Tensor | numpy.ndarray): The raw tensor or array containing mask data.
        orig_shape (tuple): Original image shape in (height, width) format.
        xy (List[numpy.ndarray]): A list of segments in pixel coordinates.
        xyn (List[numpy.ndarray]): A list of normalized segments.

    Methods:
        cpu(): Returns a copy of the Masks object with the mask tensor on CPU memory.
        numpy(): Returns a copy of the Masks object with the mask tensor as a numpy array.
        cuda(): Returns a copy of the Masks object with the mask tensor on GPU memory.
        to(*args, **kwargs): Returns a copy of the Masks object with the mask tensor on specified device and dtype.

    Examples:
        >>> masks_data = torch.rand(1, 160, 160)
        >>> orig_shape = (720, 1280)
        >>> masks = Masks(masks_data, orig_shape)
        >>> pixel_coords = masks.xy
        >>> normalized_coords = masks.xyn
    """

    def __init__(self, masks, orig_shape) -> None:
        """
        Initialize the Masks class with detection mask data and the original image shape.

        Args:
            masks (torch.Tensor | np.ndarray): Detection masks with shape (num_masks, height, width).
            orig_shape (tuple): The original image shape as (height, width). Used for normalization.

        Examples:
            >>> import torch
            >>> from ultralytics.engine.results import Masks
            >>> masks = torch.rand(10, 160, 160)  # 10 masks of 160x160 resolution
            >>> orig_shape = (720, 1280)  # Original image shape
            >>> mask_obj = Masks(masks, orig_shape)
        """
        if masks.ndim == 2:
            masks = masks[None, :]
        super().__init__(masks, orig_shape)

    @property
    @lru_cache(maxsize=1)
    def xyn(self):
        """
        Returns normalized xy-coordinates of the segmentation masks.

        This property calculates and caches the normalized xy-coordinates of the segmentation masks. The coordinates
        are normalized relative to the original image shape.

        Returns:
            (List[numpy.ndarray]): A list of numpy arrays, where each array contains the normalized xy-coordinates
                of a single segmentation mask. Each array has shape (N, 2), where N is the number of points in the
                mask contour.

        Examples:
            >>> results = model("image.jpg")
            >>> masks = results[0].masks
            >>> normalized_coords = masks.xyn
            >>> print(normalized_coords[0])  # Normalized coordinates of the first mask
        """
        return [
            scale_coords(self.data.shape[1:], x, self.orig_shape, normalize=True)
            for x in masks2segments(self.data)
        ]

    @property
    @lru_cache(maxsize=1)
    def xy(self):
        """
        Returns the [x, y] pixel coordinates for each segment in the mask tensor.

        This property calculates and returns a list of pixel coordinates for each segmentation mask in the
        Masks object. The coordinates are scaled to match the original image dimensions.

        Returns:
            (List[numpy.ndarray]): A list of numpy arrays, where each array contains the [x, y] pixel
                coordinates for a single segmentation mask. Each array has shape (N, 2), where N is the
                number of points in the segment.

        Examples:
            >>> results = model("image.jpg")
            >>> masks = results[0].masks
            >>> xy_coords = masks.xy
            >>> print(len(xy_coords))  # Number of masks
            >>> print(xy_coords[0].shape)  # Shape of first mask's coordinates
        """
        return [
            scale_coords(self.data.shape[1:], x, self.orig_shape, normalize=False)
            for x in masks2segments(self.data)
        ]



def clip_boxes(boxes, shape):
    """
    Takes a list of bounding boxes and a shape (height, width) and clips the bounding boxes to the shape.

    Args:
        boxes (torch.Tensor): The bounding boxes to clip.
        shape (tuple): The shape of the image.

    Returns:
        (torch.Tensor | numpy.ndarray): The clipped boxes.
    """
    if isinstance(boxes, torch.Tensor):  # faster individually (WARNING: inplace .clamp_() Apple MPS bug)
        boxes[..., 0] = boxes[..., 0].clamp(0, shape[1])  # x1
        boxes[..., 1] = boxes[..., 1].clamp(0, shape[0])  # y1
        boxes[..., 2] = boxes[..., 2].clamp(0, shape[1])  # x2
        boxes[..., 3] = boxes[..., 3].clamp(0, shape[0])  # y2
    else:  # np.array (faster grouped)
        boxes[..., [0, 2]] = boxes[..., [0, 2]].clip(0, shape[1])  # x1, x2
        boxes[..., [1, 3]] = boxes[..., [1, 3]].clip(0, shape[0])  # y1, y2
    return boxes


class Results(SimpleClass):

    """
    A class for storing and manipulating inference results.

    This class encapsulates the functionality for handling detection, segmentation, pose estimation,
    and classification results from YOLO models.

    Attributes:
        orig_img (numpy.ndarray): Original image as a numpy array.
        orig_shape (Tuple[int, int]): Original image shape in (height, width) format.
        boxes (Boxes | None): Object containing detection bounding boxes.
        masks (Masks | None): Object containing detection masks.
        probs (Probs | None): Object containing class probabilities for classification tasks.
        keypoints (Keypoints | None): Object containing detected keypoints for each object.
        obb (OBB | None): Object containing oriented bounding boxes.
        speed (Dict[str, float | None]): Dictionary of preprocess, inference, and postprocess speeds.
        names (Dict[int, str]): Dictionary mapping class IDs to class names.
        path (str): Path to the image file.
        _keys (Tuple[str, ...]): Tuple of attribute names for internal use.

    Methods:
        update: Updates object attributes with new detection results.
        cpu: Returns a copy of the Results object with all tensors on CPU memory.
        numpy: Returns a copy of the Results object with all tensors as numpy arrays.
        cuda: Returns a copy of the Results object with all tensors on GPU memory.
        to: Returns a copy of the Results object with tensors on a specified device and dtype.
        new: Returns a new Results object with the same image, path, and names.
        plot: Plots detection results on an input image, returning an annotated image.
        show: Shows annotated results on screen.
        save: Saves annotated results to file.
        verbose: Returns a log string for each task, detailing detections and classifications.
        save_txt: Saves detection results to a text file.
        save_crop: Saves cropped detection images.
        tojson: Converts detection results to JSON format.

    Examples:
        >>> results = model("path/to/image.jpg")
        >>> for result in results:
        ...     print(result.boxes)  # Print detection boxes
        ...     result.show()  # Display the annotated image
        ...     result.save(filename="result.jpg")  # Save annotated image
    """

    def __init__(
        self, orig_img, path, names, boxes=None, masks=None, probs=None, keypoints=None, obb=None, speed=None
    ) -> None:
        """
        Initialize the Results class for storing and manipulating inference results.

        Args:
            orig_img (numpy.ndarray): The original image as a numpy array.
            path (str): The path to the image file.
            names (Dict): A dictionary of class names.
            boxes (torch.Tensor | None): A 2D tensor of bounding box coordinates for each detection.
            masks (torch.Tensor | None): A 3D tensor of detection masks, where each mask is a binary image.
            probs (torch.Tensor | None): A 1D tensor of probabilities of each class for classification task.
            keypoints (torch.Tensor | None): A 2D tensor of keypoint coordinates for each detection.
            obb (torch.Tensor | None): A 2D tensor of oriented bounding box coordinates for each detection.
            speed (Dict | None): A dictionary containing preprocess, inference, and postprocess speeds (ms/image).

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> result = results[0]  # Get the first result
            >>> boxes = result.boxes  # Get the boxes for the first result
            >>> masks = result.masks  # Get the masks for the first result

        Notes:
            For the default pose model, keypoint indices for human body pose estimation are:
            0: Nose, 1: Left Eye, 2: Right Eye, 3: Left Ear, 4: Right Ear
            5: Left Shoulder, 6: Right Shoulder, 7: Left Elbow, 8: Right Elbow
            9: Left Wrist, 10: Right Wrist, 11: Left Hip, 12: Right Hip
            13: Left Knee, 14: Right Knee, 15: Left Ankle, 16: Right Ankle
        """
        self.orig_img = orig_img
        self.orig_shape = orig_img.shape[:2]
        self.boxes = Boxes(boxes, self.orig_shape) if boxes is not None else None  # native size boxes
        self.masks = Masks(masks, self.orig_shape) if masks is not None else None  # native size or imgsz masks
        self.probs = Probs(probs) if probs is not None else None
        self.speed = speed if speed is not None else {"preprocess": None, "inference": None, "postprocess": None}
        self.names = names
        self.path = path
        self.save_dir = None
        self._keys = "boxes", "masks", "probs", "keypoints", "obb"

    def __getitem__(self, idx):
        """
        Return a Results object for a specific index of inference results.

        Args:
            idx (int | slice): Index or slice to retrieve from the Results object.

        Returns:
            (Results): A new Results object containing the specified subset of inference results.

        Examples:
            >>> results = model("path/to/image.jpg")  # Perform inference
            >>> single_result = results[0]  # Get the first result
            >>> subset_results = results[1:4]  # Get a slice of results
        """
        return self._apply("__getitem__", idx)

    def __len__(self):
        """
        Return the number of detections in the Results object.

        Returns:
            (int): The number of detections, determined by the length of the first non-empty attribute
                (boxes, masks, probs, keypoints, or obb).

        Examples:
            >>> results = Results(orig_img, path, names, boxes=torch.rand(5, 4))
            >>> len(results)
            5
        """
        for k in self._keys:
            v = getattr(self, k)
            if v is not None:
                return len(v)

    def update(self, boxes=None, masks=None, probs=None, obb=None, keypoints=None):
        """
        Updates the Results object with new detection data.

        This method allows updating the boxes, masks, probabilities, and oriented bounding boxes (OBB) of the
        Results object. It ensures that boxes are clipped to the original image shape.

        Args:
            boxes (torch.Tensor | None): A tensor of shape (N, 6) containing bounding box coordinates and
                confidence scores. The format is (x1, y1, x2, y2, conf, class).
            masks (torch.Tensor | None): A tensor of shape (N, H, W) containing segmentation masks.
            probs (torch.Tensor | None): A tensor of shape (num_classes,) containing class probabilities.
            obb (torch.Tensor | None): A tensor of shape (N, 5) containing oriented bounding box coordinates.
            keypoints (torch.Tensor | None): A tensor of shape (N, 17, 3) containing keypoints.

        Examples:
            >>> results = model("image.jpg")
            >>> new_boxes = torch.tensor([[100, 100, 200, 200, 0.9, 0]])
            >>> results[0].update(boxes=new_boxes)
        """
        if boxes is not None:
            self.boxes = Boxes(clip_boxes(boxes, self.orig_shape), self.orig_shape)
        if masks is not None:
            self.masks = Masks(masks, self.orig_shape)
        if probs is not None:
            self.probs = probs


    def _apply(self, fn, *args, **kwargs):
        """
        Applies a function to all non-empty attributes and returns a new Results object with modified attributes.

        This method is internally called by methods like .to(), .cuda(), .cpu(), etc.

        Args:
            fn (str): The name of the function to apply.
            *args (Any): Variable length argument list to pass to the function.
            **kwargs (Any): Arbitrary keyword arguments to pass to the function.

        Returns:
            (Results): A new Results object with attributes modified by the applied function.

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> for result in results:
            ...     result_cuda = result.cuda()
            ...     result_cpu = result.cpu()
        """
        r = self.new()
        for k in self._keys:
            v = getattr(self, k)
            if v is not None:
                setattr(r, k, getattr(v, fn)(*args, **kwargs))
        return r

    def cpu(self):
        """
        Returns a copy of the Results object with all its tensors moved to CPU memory.

        This method creates a new Results object with all tensor attributes (boxes, masks, probs, keypoints, obb)
        transferred to CPU memory. It's useful for moving data from GPU to CPU for further processing or saving.

        Returns:
            (Results): A new Results object with all tensor attributes on CPU memory.

        Examples:
            >>> results = model("path/to/image.jpg")  # Perform inference
            >>> cpu_result = results[0].cpu()  # Move the first result to CPU
            >>> print(cpu_result.boxes.device)  # Output: cpu
        """
        return self._apply("cpu")

    def numpy(self):
        """
        Converts all tensors in the Results object to numpy arrays.

        Returns:
            (Results): A new Results object with all tensors converted to numpy arrays.

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> numpy_result = results[0].numpy()
            >>> type(numpy_result.boxes.data)
            <class 'numpy.ndarray'>

        Notes:
            This method creates a new Results object, leaving the original unchanged. It's useful for
            interoperability with numpy-based libraries or when CPU-based operations are required.
        """
        return self._apply("numpy")

    def cuda(self):
        """
        Moves all tensors in the Results object to GPU memory.

        Returns:
            (Results): A new Results object with all tensors moved to CUDA device.

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> cuda_results = results[0].cuda()  # Move first result to GPU
            >>> for result in results:
            ...     result_cuda = result.cuda()  # Move each result to GPU
        """
        return self._apply("cuda")

    def to(self, *args, **kwargs):
        """
        Moves all tensors in the Results object to the specified device and dtype.

        Args:
            *args (Any): Variable length argument list to be passed to torch.Tensor.to().
            **kwargs (Any): Arbitrary keyword arguments to be passed to torch.Tensor.to().

        Returns:
            (Results): A new Results object with all tensors moved to the specified device and dtype.

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> result_cuda = results[0].to("cuda")  # Move first result to GPU
            >>> result_cpu = results[0].to("cpu")  # Move first result to CPU
            >>> result_half = results[0].to(dtype=torch.float16)  # Convert first result to half precision
        """
        return self._apply("to", *args, **kwargs)

    def new(self):
        """
        Creates a new Results object with the same image, path, names, and speed attributes.

        Returns:
            (Results): A new Results object with copied attributes from the original instance.

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> new_result = results[0].new()
        """
        return Results(orig_img=self.orig_img, path=self.path, names=self.names, speed=self.speed)


    def verbose(self):
        """
        Returns a log string for each task in the results, detailing detection and classification outcomes.

        This method generates a human-readable string summarizing the detection and classification results. It includes
        the number of detections for each class and the top probabilities for classification tasks.

        Returns:
            (str): A formatted string containing a summary of the results. For detection tasks, it includes the
                number of detections per class. For classification tasks, it includes the top 5 class probabilities.

        Examples:
            >>> results = model("path/to/image.jpg")
            >>> for result in results:
            >>>     print(result.verbose())
            2 persons, 1 car, 3 traffic lights,
            dog 0.92, cat 0.78, horse 0.64,

        Notes:
            - If there are no detections, the method returns "(no detections), " for detection tasks.
            - For classification tasks, it returns the top 5 class probabilities and their corresponding class names.
            - The returned string is comma-separated and ends with a comma and a space.
        """
        log_string = ""
        probs = self.probs
        if len(self) == 0:
            return log_string if probs is not None else f"{log_string}(no detections), "
        if probs is not None:
            log_string += f"{', '.join(f'{self.names[j]} {probs.data[j]:.2f}' for j in probs.top5)}, "
        if boxes := self.boxes:
            for c in boxes.cls.unique():
                n = (boxes.cls == c).sum()  # detections per class
                log_string += f"{n} {self.names[int(c)]}{'s' * (n > 1)}, "
        return log_string




def convert_torch2numpy_batch(batch: torch.Tensor) -> np.ndarray:
    """
    Convert a batch of FP32 torch tensors (0.0-1.0) to a NumPy uint8 array (0-255), changing from BCHW to BHWC layout.

    Args:
        batch (torch.Tensor): Input tensor batch of shape (Batch, Channels, Height, Width) and dtype torch.float32.

    Returns:
        (np.ndarray): Output NumPy array batch of shape (Batch, Height, Width, Channels) and dtype uint8.
    """
    return (batch.permute(0, 2, 3, 1).contiguous() * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()





class Model:
    def __init__(self, model_path='best.onnx', use_cuda=True):
        so = ort.SessionOptions()
        # Uncomment to see detailed logs about Memcpy nodes, kernel selection, etc.
        # so.log_severity_level = 1  # 0=VERBOSE, 1=INFO, 2=WARNING, ...

        providers = ['CPUExecutionProvider']
        if use_cuda:
            providers.insert(0, 'CUDAExecutionProvider')
            print(f'using cuda')

        self.session = ort.InferenceSession(model_path, sess_options=so, providers=providers)
        self.input_name = self.session.get_inputs()[0].name  # don't hard-code 'images'
        self.metadata = self.session.get_modelmeta().custom_metadata_map
        self.names = self.metadata['names']
        self.imgsz = ast.literal_eval(self.metadata['imgsz'])

        print(self.names, self.imgsz)
        

        self.transform  = T.Compose([
        T.Resize(size=self.imgsz, interpolation=T.InterpolationMode.BILINEAR, antialias=True),
        T.ToTensor(),
        T.Normalize(mean=[0.4850, 0.4560, 0.4060], std=[0.2290, 0.2240, 0.2250])])
        self.transform2 = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=[0.4850, 0.4560, 0.4060], std=[0.2290, 0.2240, 0.2250])])


    def __preprocess(self, im):
        """
        Prepares input image before inference.

        Args:
            im (torch.Tensor | List(np.ndarray)): BCHW for tensor, [(HWC) x B] for list.
        """
        
        img_rgb = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))

        preprocessed = self.transform(img_rgb).unsqueeze(0)

        return preprocessed
    
    def __preprocess_cv2(self, im):
        img_rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        img_rgb = cv2.resize(img_rgb, self.imgsz, interpolation=cv2.INTER_LINEAR)
        img_rgb = np.float32(img_rgb) / 255.0
        return img_rgb
    
    def __preprocess_cv2_torch(self, im):
        img_rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        img_rgb = cv2.resize(img_rgb, self.imgsz, interpolation=cv2.INTER_LINEAR)
        img_rgb = Image.fromarray(img_rgb)
        preprocessed = self.transform2(img_rgb).unsqueeze(0)
        return preprocessed

    def __call__(self, image):
        # Keep a copy of the original image for postprocess/visualization
        orig = image.copy()

        # Your preprocess can return either np.ndarray or torch.Tensor
        start = time.time()
        #img_pre = self.__preprocess(image)
        img_pre = self.__preprocess_cv2_torch(image)

       
        #img_pre = self.__preprocess_cv2(image)
        tempo = time.time() - start

        print(f'preprocessing time is {tempo*1000} ms')

        # Ensure NumPy float32, NCHW, with batch dimension
        arr = img_pre.detach().cpu().numpy() if isinstance(img_pre, torch.Tensor) else img_pre
        if arr.dtype != np.float32:
            arr = arr.astype(np.float32)

        if arr.ndim == 3:  # (C,H,W) or (H,W,C)
            if arr.shape[0] in (1, 3):        # (C,H,W)
                arr = arr[None, ...]          # -> (1,C,H,W)
            else:                              # (H,W,C)
                arr = arr.transpose(2, 0, 1)[None, ...]
        elif arr.ndim != 4:
            raise ValueError(f"Unexpected input shape {arr.shape}; expected (N,C,H,W)")

        #print(arr.shape)
        # Inference
        start = time.time()
        ort_outs = self.session.run(None, {self.input_name: arr})
        tempo = time.time() - start
        print(f'inference time is {tempo*1000} ms')


        # Convert outputs to torch if your postprocess expects torch tensors
        outputs = [torch.from_numpy(o) if isinstance(o, np.ndarray) else torch.tensor(o) for o in ort_outs]

        # Use the local original image, not a global
        start = time.time()
        results = self.__postprocess(outputs, img_pre, [orig])
        tempo = time.time() - start
        print(f'postprocess time is {tempo*1000} ms')


        if len(results) > 0:
            results = results[0]

        return results
    
    def __postprocess(self, preds, img, orig_imgs):
        """Post-processes predictions to return Results objects."""
        if not isinstance(orig_imgs, list):  # input images are a torch.Tensor, not a list
            orig_imgs = convert_torch2numpy_batch(orig_imgs)

        preds = preds[0] if isinstance(preds, (list, tuple)) else preds
        return [
            Results(orig_img, path=img_path, names=self.names, probs=pred)
            for pred, orig_img, img_path in zip(preds, orig_imgs, self.metadata['batch'])
        ]
