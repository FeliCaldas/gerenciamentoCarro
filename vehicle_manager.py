import base64
from PIL import Image
from io import BytesIO

def save_image(image_file):
    """
    Convert uploaded image to base64 string for storage
    """
    if image_file is None:
        return None
        
    try:
        # Open and compress the image
        image = Image.open(image_file)
        max_size = (800, 800)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # Convert to JPEG format
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85, optimize=True)
        image_bytes = buffer.getvalue()
        
        # Convert to base64
        return base64.b64encode(image_bytes).decode()
    except Exception as e:
        raise Exception(f"Erro ao processar imagem: {str(e)}")
