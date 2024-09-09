import os
import argparse
from PIL import Image
import numpy as np
import cv2
from basicsr.archs.rrdbnet_arch import RRDBNet
from basicsr.utils.download_util import load_file_from_url
from realesrgan import RealESRGANer
import torch

def maintain_aspect_ratio(image, target_width, target_height):
    h, w = image.shape[:2]
    aspect = w / h

    if w < h:
        new_width = target_width
        new_height = int(new_width / aspect)
    else:
        new_height = target_height
        new_width = int(new_height * aspect)

    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

def process_images(input_dir, model_name='RealESRGAN_x4plus', tile=0, tile_pad=10, pre_pad=0):
    # Initialize the RealESRGAN model
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    netscale = 4
    file_url = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
    model_path = load_file_from_url(url=file_url, model_dir='weights', progress=True, file_name=None)

    # Use CUDA if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    upsampler = RealESRGANer(scale=netscale, model_path=model_path, model=model, tile=tile, tile_pad=tile_pad, pre_pad=pre_pad, device=device)

    # Process images in the input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            input_path = os.path.join(input_dir, filename)
            
            # Open the image and check its size
            with Image.open(input_path) as img:
                width, height = img.size
                
                # Only process images below 1920x1080
                if width < 1920 or height < 1080:
                    print(f"Processing {filename}...")
                    
                    # Upscale the image
                    output, _ = upsampler.enhance(input_path, outscale=4)
                    
                    # Maintain aspect ratio and ensure at least 1920x1080
                    output = maintain_aspect_ratio(output, 1920, 1080)
                    
                    # If the image is smaller than 1920x1080 after maintaining aspect ratio,
                    # pad it to reach 1920x1080
                    h, w = output.shape[:2]
                    if w < 1920 or h < 1080:
                        top = bottom = (1080 - h) // 2
                        left = right = (1920 - w) // 2
                        output = cv2.copyMakeBorder(output, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])
                    
                    # Save the upscaled image, overwriting the original
                    cv2.imwrite(input_path, output)
                    print(f"Upscaled {filename} to at least 1920x1080 while maintaining aspect ratio")
                else:
                    print(f"Skipping {filename} (already 1920x1080 or larger)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upscale images in a directory to at least 1920x1080 using Real-ESRGAN while maintaining aspect ratio")
    parser.add_argument("input_dir", help="Input directory containing images")
    parser.add_argument("--model", default="RealESRGAN_x4plus", help="Model name (default: RealESRGAN_x4plus)")
    parser.add_argument("--tile", type=int, default=0, help="Tile size (0 for no tiling, default: 0)")
    parser.add_argument("--tile_pad", type=int, default=10, help="Tile padding (default: 10)")
    parser.add_argument("--pre_pad", type=int, default=0, help="Pre padding (default: 0)")
    
    args = parser.parse_args()
    
    process_images(args.input_dir, args.model, args.tile, args.tile_pad, args.pre_pad)

