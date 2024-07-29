import subprocess
import tensorrt as trt
import os

TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

def get_engine(model_file='weights/best_placa_static.onnx', engine_file='weights/model.plan', fp16=True, verbose=True):
    EXPLICIT_BATCH = 1 << (int)(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    with trt.Builder(TRT_LOGGER) as builder, builder.create_network(EXPLICIT_BATCH) as network, builder.create_builder_config() as config,\
        trt.OnnxParser(network,TRT_LOGGER) as parser:
        
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)

        if fp16:
            print("[INFO] Open FP16 Mode!")
            config.set_flag(trt.BuilderFlag.FP16)

        with open(model_file, 'rb') as model:
            parser.parse(model.read())
        if verbose:
            print(">"*50)
            for error in range(parser.num_errors):
                print(parser.get_error(error))

        network.get_input(0).shape = [ 1, 3, 2048, 3072 ]

        # builder engine
        engine = builder.build_engine(network, config)
        print("[INFO] Completed creating Engine!")
        with open(engine_file, "wb") as f:
            f.write(engine.serialize())
        return engine
    
def main():

    # Caminho para o script Python que você deseja executar
    script_path = 'load_engine.py'

    # Executa o script e captura a saída
    result = subprocess.run(['python', script_path], capture_output=True, text=True)

    # Captura a saída padrão (stdout) e o erro padrão (stderr)
    stdout = result.stdout
    stderr = result.stderr

    print("Saída padrão:")
    print(stdout)

    print("Erro padrão:")
    print(stderr)

    if 'Using an engine plan file across different models of devices is not recommended and is likely to affect performance or even cause errors.' in stdout:
        #subprocess.run(['sh', 'convert.sh'], capture_output=True, text=True)
        print(f'modelo gerado em outro dispositivo')
        os.remove('weights/model.plan')
        print(f'starting build engine')
        get_engine()

     
if __name__ == '__main__':
    main()