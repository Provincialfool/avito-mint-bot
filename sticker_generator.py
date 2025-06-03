import os
import io
import logging
import aiohttp
import asyncio
import random
from PIL import Image, ImageDraw, ImageFont
import base64

# API tokens
REMOVE_BG_TOKEN = os.getenv("REMOVE_BG_TOKEN", "WLMDgqhpcCGFGD7bgiaKzuJo")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "r8_7miai9DTh96AVgIZZCjS6Jq5d4kJHsv0WmoRz")

# Festival templates (we'll generate these programmatically since we can't include binary files)
TEMPLATES = [
    {"name": "template1", "color": "#FF6B6B", "text_color": "#FFFFFF"},
    {"name": "template2", "color": "#4ECDC4", "text_color": "#FFFFFF"},
    {"name": "template3", "color": "#45B7D1", "text_color": "#FFFFFF"},
    {"name": "template4", "color": "#96CEB4", "text_color": "#FFFFFF"},
    {"name": "template5", "color": "#FFEAA7", "text_color": "#2D3436"}
]

FESTIVAL_TEXT = "Хорошие истории начинаются с тебя"
AVITO_TEXT = "Avito × Dikaya Myata"

def create_festival_template(template_info, size=(800, 800)):
    """Create a festival template programmatically"""
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Create gradient background
    for y in range(size[1]):
        alpha = int(255 * (1 - y / size[1]) * 0.8)
        color = tuple(int(template_info["color"][i:i+2], 16) for i in (1, 3, 5)) + (alpha,)
        draw.rectangle([(0, y), (size[0], y+1)], fill=color)
    
    # Add decorative border
    border_width = 20
    draw.rectangle([(0, 0), (size[0], border_width)], fill=template_info["color"])
    draw.rectangle([(0, size[1]-border_width), (size[0], size[1])], fill=template_info["color"])
    draw.rectangle([(0, 0), (border_width, size[1])], fill=template_info["color"])
    draw.rectangle([(size[0]-border_width, 0), (size[0], size[1])], fill=template_info["color"])
    
    # Add festival text at bottom
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Main text
    bbox = draw.textbbox((0, 0), FESTIVAL_TEXT, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_x = (size[0] - text_width) // 2
    text_y = size[1] - 120
    
    # Text shadow
    draw.text((text_x + 2, text_y + 2), FESTIVAL_TEXT, fill=(0, 0, 0, 128), font=font_large)
    draw.text((text_x, text_y), FESTIVAL_TEXT, fill=template_info["text_color"], font=font_large)
    
    # Avito text
    bbox = draw.textbbox((0, 0), AVITO_TEXT, font=font_small)
    text_width = bbox[2] - bbox[0]
    text_x = (size[0] - text_width) // 2
    text_y = size[1] - 60
    
    draw.text((text_x + 1, text_y + 1), AVITO_TEXT, fill=(0, 0, 0, 128), font=font_small)
    draw.text((text_x, text_y), AVITO_TEXT, fill=template_info["text_color"], font=font_small)
    
    return img

async def remove_background(image_bytes):
    """Remove background using Remove.bg API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.remove.bg/v1.0/removebg',
                headers={'X-Api-Key': REMOVE_BG_TOKEN},
                data=aiohttp.FormData()._add_field('image_file', image_bytes, content_type='image/jpeg')
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logging.error(f"Remove.bg API error: {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Error removing background: {e}")
        return None

def composite_images(background_img, foreground_bytes):
    """Composite foreground image onto background template"""
    try:
        # Load foreground image (person with removed background)
        foreground_img = Image.open(io.BytesIO(foreground_bytes)).convert('RGBA')
        
        # Calculate size to fit person in the center area of template
        bg_width, bg_height = background_img.size
        
        # Reserve space for text at bottom (about 150px)
        available_height = bg_height - 200
        available_width = bg_width - 100  # Some padding
        
        # Scale foreground to fit
        fg_width, fg_height = foreground_img.size
        scale_w = available_width / fg_width
        scale_h = available_height / fg_height
        scale = min(scale_w, scale_h, 1.0)  # Don't upscale
        
        new_width = int(fg_width * scale)
        new_height = int(fg_height * scale)
        
        foreground_img = foreground_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Position in center of available space
        x = (bg_width - new_width) // 2
        y = (available_height - new_height) // 2 + 50  # Slight offset from top
        
        # Create final composite
        result = background_img.copy()
        result.paste(foreground_img, (x, y), foreground_img)
        
        return result
    except Exception as e:
        logging.error(f"Error compositing images: {e}")
        return None

async def generate_sticker(photo_bytes):
    """Generate a festival sticker from user photo"""
    try:
        # Step 1: Remove background
        logging.info("Removing background from photo...")
        no_bg_bytes = await remove_background(photo_bytes)
        
        if not no_bg_bytes:
            logging.error("Failed to remove background")
            return None, None
        
        # Step 2: Choose random template
        template_info = random.choice(TEMPLATES)
        logging.info(f"Using template: {template_info['name']}")
        
        # Step 3: Create template
        background_img = create_festival_template(template_info)
        
        # Step 4: Composite images
        final_img = composite_images(background_img, no_bg_bytes)
        
        if not final_img:
            logging.error("Failed to composite images")
            return None, None
        
        # Step 5: Convert to bytes
        output_buffer = io.BytesIO()
        final_img.save(output_buffer, format='PNG', quality=95)
        output_buffer.seek(0)
        
        logging.info("Sticker generated successfully")
        return output_buffer.getvalue(), template_info['name']
        
    except Exception as e:
        logging.error(f"Error generating sticker: {e}")
        return None, None

# Alternative simple sticker generator if APIs fail
def generate_simple_sticker(photo_bytes, template_info):
    """Generate a simple sticker without background removal"""
    try:
        # Load user photo
        user_img = Image.open(io.BytesIO(photo_bytes)).convert('RGB')
        
        # Create template
        template_img = create_festival_template(template_info, size=(600, 800))
        
        # Resize user photo to fit in upper portion
        user_width, user_height = user_img.size
        template_width, template_height = template_img.size
        
        # Available space for photo (leave room for text)
        available_height = template_height - 200
        available_width = template_width - 100
        
        # Scale to fit
        scale_w = available_width / user_width
        scale_h = available_height / user_height
        scale = min(scale_w, scale_h)
        
        new_width = int(user_width * scale)
        new_height = int(user_height * scale)
        
        user_img = user_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (new_width, new_height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, new_width, new_height), fill=255)
        
        # Apply circular mask
        output = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        output.paste(user_img, (0, 0))
        output.putalpha(mask)
        
        # Paste onto template
        x = (template_width - new_width) // 2
        y = 80  # Fixed position from top
        
        template_img.paste(output, (x, y), output)
        
        # Convert to bytes
        output_buffer = io.BytesIO()
        template_img.save(output_buffer, format='PNG', quality=95)
        output_buffer.seek(0)
        
        return output_buffer.getvalue()
        
    except Exception as e:
        logging.error(f"Error generating simple sticker: {e}")
        return None
