import argparse
import os
import sys
import time

import gradio as gr
import ray
import torch

current_file_path = os.path.abspath(__file__)
project_roots = [os.path.dirname(current_file_path), os.path.dirname(os.path.dirname(current_file_path)), os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))]
for project_root in project_roots:
    sys.path.insert(0, project_root) if project_root not in sys.path else None

from videox_fun.api.api_multi_nodes import (MultiNodesEngine,
                                           multi_nodes_infer_forward_api)
from videox_fun.ui.controller import flow_scheduler_dict
from videox_fun.ui.wan_fun_ui import Wan_Fun_Controller

def main():
    parser = argparse.ArgumentParser(description='xDiT HTTP Service')
    parser.add_argument('--world_size', type=int, default=8, help='Number of parallel workers')
    parser.add_argument('--gpu_memory_mode', type=str, default="model_full_load", help='GPU memory mode')
    parser.add_argument('--ulysses_degree', type=int, default=4, help='Degree of Ulysses configuration')
    parser.add_argument('--ring_degree', type=int, default=2, help='Degree of Ring configuration')
    parser.add_argument('--weight_dtype', type=str, default='bf16', help='Weight data type')
    parser.add_argument('--server_name', type=str, default="0.0.0.0", help='Server IP address')
    parser.add_argument('--server_port', type=int, default=7860, help='Server Port')
    parser.add_argument('--config_path', type=str, default="config/wan2.1/wan_civitai.yaml", help='Path to config file')
    parser.add_argument('--model_name', type=str, default="models/Diffusion_Transformer/Wan2.1-Fun-V1.1-1.3B-InP", help='Model path')
    parser.add_argument('--model_type', type=str, default="Inpaint", help='Model type (Inpaint/Control)')
    parser.add_argument('--savedir_sample', type=str, default=None, help='The save directory for samples')
    args = parser.parse_args()

    weight_dtype = torch.float32
    if args.weight_dtype == "bf16":
        weight_dtype = torch.bfloat16
    elif args.weight_dtype == "fp16":
        weight_dtype = torch.float16

    engine = MultiNodesEngine(
        world_size=args.world_size, Controller=Wan_Fun_Controller,
        GPU_memory_mode=args.gpu_memory_mode, scheduler_dict=flow_scheduler_dict, model_name=args.model_name, model_type=args.model_type, config_path=args.config_path, 
        ulysses_degree=args.ulysses_degree, ring_degree=args.ring_degree, weight_dtype=weight_dtype, savedir_sample=args.savedir_sample,
    )
    
    def gr_launch():
        # launch gradio
        with gr.Blocks() as demo:
            gr.Markdown("")
        app, _, _ = demo.queue(status_update_rate=1).launch(
            server_name=args.server_name,
            server_port=args.server_port,
            prevent_thread_lock=True
        )
        
        # launch api
        multi_nodes_infer_forward_api(None, app, engine)

    gr_launch()

    # not close the python
    while True:
        time.sleep(5)

if __name__ == "__main__":
    main()