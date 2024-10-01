import cv2


imagem = cv2.imread('Fluxo_sistema/omni7_20220310_135536_72777123_Panoramic_000699_4113_061-6373.jpg')

height, width = imagem.shape[:2]
#imagem = imagem[:, 1*width//16:7*width//16]
imagem = imagem[:, 9*width//16:15*width//16]

cv2.imwrite('direita.jpg', imagem)