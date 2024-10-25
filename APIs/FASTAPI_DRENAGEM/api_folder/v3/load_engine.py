import tensorrt as trt

TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

def load_engine(engine_file_path):
    with open(engine_file_path, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
        return runtime.deserialize_cuda_engine(f.read())
    

if __name__ == '__main__':
    engine = load_engine('v3/weights/model.plan')

