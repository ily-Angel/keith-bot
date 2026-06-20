import discord
from discord.ext import commands
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageChops, ImageFont, ImageEnhance, ImageSequence, ImageOps
from database_sql import AsyncSessionReze, BorderOptions, ModeOfTheBorderEditor
from sqlalchemy import select, func
import math
import random
import numpy as np
import aiohttp
import os
import io
from rembg import remove
import asyncio

def add_circular_glow_neon(image: Image.Image, output_path=None, border_width=20, 
                          glow_color='#00FF00', glow_intensity=10):
    """
    Adiciona borda com efeito Glow Neon circular à imagem PIL.
    
    Args:
        image (Image.Image): Imagem PIL de entrada
        output_path (str): Caminho de saída (opcional)
        border_width (int): Largura da borda glow
        glow_color (str/tuple): Cor do glow neon (hex ou RGB)
        glow_intensity (int): Intensidade do efeito glow (1-20)
    
    Returns:
        PIL.Image.Image: Imagem com borda glow neon circular
    """
    
    try:
        # Converter cor para RGB
        def hex_to_rgb(hex_color):
            if isinstance(hex_color, str) and hex_color.startswith('#'):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return hex_color
        
        neon_rgb = hex_to_rgb(glow_color)
        
        # Converter imagem original para RGBA
        original = image.convert("RGBA")
        orig_width, orig_height = original.size
        
        # Garantir que a imagem seja quadrada para círculo perfeito
        size = max(orig_width, orig_height)
        
        # Criar imagem quadrada para o círculo
        square_original = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        
        # Centralizar a imagem original no quadrado
        x_offset = (size - orig_width) // 2
        y_offset = (size - orig_height) // 2
        square_original.paste(original, (x_offset, y_offset))
        
        # Calcular novo tamanho com borda
        new_size = size + 2 * border_width
        
        # Criar máscara circular para o glow
        def create_circular_mask(diameter, inner_diameter=0):
            mask = Image.new('L', (diameter, diameter), 0)
            draw = ImageDraw.Draw(mask)
            
            # Desenhar círculo externo
            draw.ellipse([0, 0, diameter, diameter], fill=255)
            
            # Criar furo interno se especificado
            if inner_diameter > 0:
                inner_offset = (diameter - inner_diameter) // 2
                draw.ellipse([
                    inner_offset, inner_offset, 
                    inner_offset + inner_diameter, inner_offset + inner_diameter
                ], fill=0)
            
            return mask
        
        # Criar gradiente de glow circular
        def create_circular_glow_gradient():
            gradient_layer = Image.new('RGBA', (new_size, new_size), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient_layer)
            
            # Máscara para a área do glow (anel circular)
            glow_mask = create_circular_mask(new_size, size)
            
            # Aplicar gradiente radial
            center = new_size / 2
            max_radius = new_size / 2
            
            for y in range(new_size):
                for x in range(new_size):
                    if glow_mask.getpixel((x, y)) > 0:  # apenas onde tem glow
                        distance = math.sqrt((x - center)**2 + (y - center)**2)
                        
                        # Calcular alpha baseado na distância do centro
                        inner_radius = size / 2
                        outer_radius = new_size / 2
                        
                        if distance >= inner_radius and distance <= outer_radius:
                            # Gradiente do interior para o exterior do anel
                            progress = (distance - inner_radius) / (outer_radius - inner_radius)
                            alpha = int(255 * (1 - progress))  # Mais forte perto da imagem
                        else:
                            alpha = 0
                        
                        if alpha > 0:
                            gradient_draw.point(
                                (x, y), 
                                fill=(neon_rgb[0], neon_rgb[1], neon_rgb[2], alpha)
                            )
            
            return gradient_layer
        
        # Criar máscara circular para a imagem original
        image_mask = create_circular_mask(size)
        circular_original = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        circular_original.putalpha(image_mask)
        circular_original.paste(square_original, (0, 0), square_original)
        
        # Criar camadas de glow
        glow_layers = []
        
        # Camada base
        base_glow = create_circular_glow_gradient()
        glow_layers.append(base_glow)
        
        # Camadas adicionais para intensidade
        for i in range(glow_intensity):
            blur_radius = (i + 1) * 3
            blurred_glow = base_glow.filter(ImageFilter.GaussianBlur(blur_radius))
            glow_layers.append(blurred_glow)
        
        # Combinar todas as camadas de glow
        final_glow = Image.new('RGBA', (new_size, new_size), (0, 0, 0, 0))
        for layer in glow_layers:
            final_glow = Image.alpha_composite(final_glow, layer)
        
        # Criar imagem final
        result_image = Image.new('RGBA', (new_size, new_size), (0, 0, 0, 0))
        
        # Aplicar glow
        result_image = Image.alpha_composite(result_image, final_glow)
        
        # Colocar imagem circular original no centro
        image_offset = (new_size - size) // 2
        result_image.paste(circular_original, (image_offset, image_offset), circular_original)
        
        # Salvar se output_path for especificado
        if output_path:
            result_image.save(output_path, 'PNG')
        
        # SEMPRE retornar a imagem
        return result_image
        
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        # Em caso de erro, retornar a imagem original como fallback
        return image.convert("RGBA")

# Versão simplificada e segura
async def add_circular_glow_neon_async(image: Image.Image, output_path=None, border_width=20, 
                                     glow_color='#00FF00', glow_intensity=10):
    """
    Versão async segura da função de glow neon circular.
    """
    try:
        # Chamar a função síncrona
        result = add_circular_glow_neon(
            image=image,
            output_path=output_path,
            border_width=border_width,
            glow_color=glow_color,
            glow_intensity=glow_intensity
        )
        
        # Garantir que não retorne None
        if result is None:
            return image.convert("RGBA")
        
        return result
        
    except Exception as e:
        print(f"Erro na versão async: {e}")
        return image.convert("RGBA")


def add_gradient_border(image: Image.Image, output_path=None, border_width=20, 
                       start_color='#FF0000', end_color='#0000FF', 
                       gradient_direction='horizontal', corner_radius=0):
    """
    Adiciona borda com gradiente à imagem PIL.
    
    Args:
        image (Image.Image): Imagem PIL de entrada
        output_path (str): Caminho de saída (opcional)
        border_width (int): Largura da borda
        start_color (str/tuple): Cor inicial do gradiente (hex ou RGB)
        end_color (str/tuple): Cor final do gradiente (hex ou RGB)
        gradient_direction (str): 'horizontal', 'vertical', 'diagonal', 'radial'
        corner_radius (int): Raio dos cantos
    
    Returns:
        PIL.Image.Image: Imagem com borda gradiente
    """
    
    # Converter cores para RGB
    def hex_to_rgb(hex_color):
        if isinstance(hex_color, str) and hex_color.startswith('#'):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return hex_color
    
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)
    
    # Converter imagem original para RGBA
    original = image.convert("RGBA")
    orig_width, orig_height = original.size
    
    # Calcular novo tamanho
    new_width = orig_width + 2 * border_width
    new_height = orig_height + 2 * border_width
    
    # Criar imagem para o gradiente
    gradient_image = Image.new('RGB', (new_width, new_height))
    draw = ImageDraw.Draw(gradient_image)
    
    # Funções para diferentes tipos de gradiente
    def get_horizontal_color(x, y):
        progress = x / (new_width - 1) if new_width > 1 else 0
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
        return (r, g, b)
    
    def get_vertical_color(x, y):
        progress = y / (new_height - 1) if new_height > 1 else 0
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
        return (r, g, b)
    
    def get_diagonal_color(x, y):
        progress = (x + y) / (new_width + new_height - 2) if (new_width + new_height) > 2 else 0
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
        return (r, g, b)
    
    def get_radial_color(x, y):
        center_x, center_y = new_width / 2, new_height / 2
        distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_distance = math.sqrt(center_x**2 + center_y**2)
        progress = distance / max_distance if max_distance > 0 else 0
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * progress)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * progress)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * progress)
        return (r, g, b)
    
    # Selecionar função de gradiente
    gradient_functions = {
        'horizontal': get_horizontal_color,
        'vertical': get_vertical_color,
        'diagonal': get_diagonal_color,
        'radial': get_radial_color
    }
    
    get_color = gradient_functions.get(gradient_direction, get_horizontal_color)
    
    # Método otimizado para criar gradiente
    if gradient_direction == 'horizontal':
        for x in range(new_width):
            color = get_color(x, 0)
            draw.line([(x, 0), (x, new_height)], fill=color)
    elif gradient_direction == 'vertical':
        for y in range(new_height):
            color = get_color(0, y)
            draw.line([(0, y), (new_width, y)], fill=color)
    else:
        # Para diagonal e radial, usar abordagem por linha (mais eficiente que pixel por pixel)
        for y in range(new_height):
            for x in range(new_width):
                color = get_color(x, y)
                draw.point((x, y), fill=color)
    
    # Converter para RGBA
    gradient_image = gradient_image.convert("RGBA")
    
    # Aplicar máscara para cantos arredondados se necessário
    if corner_radius > 0:
        mask = Image.new('L', (new_width, new_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        
        # Usar rounded_rectangle se disponível, caso contrário fallback para rectangle
        if hasattr(mask_draw, 'rounded_rectangle'):
            mask_draw.rounded_rectangle([0, 0, new_width, new_height], radius=corner_radius, fill=255)
        else:
            # Fallback para retângulo normal
            mask_draw.rectangle([0, 0, new_width, new_height], fill=255)
        
        gradient_image.putalpha(mask)
    
    # Colocar imagem original no centro
    gradient_image.paste(original, (border_width, border_width), original)
    
    # Salvar ou retornar
    if output_path:
        gradient_image.save(output_path)
        return gradient_image
    else:
        return gradient_image

# Versão simplificada para uso rápido
def add_simple_gradient_border(image: Image.Image, border_width=20, 
                              start_color=(255, 0, 0), end_color=(0, 0, 255),
                              direction='horizontal'):
    """
    Versão simplificada da função de borda gradiente.
    """
    return add_gradient_border(
        image=image,
        border_width=border_width,
        start_color=start_color,
        end_color=end_color,
        gradient_direction=direction
    )

async def circule_image(image: Image.Image) -> Image.Image:
    # Converter para RGBA para suportar transparência
    image = image.convert("RGBA")
    
    # Criar máscara circular
    mask = Image.new("L", image.size, color=0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([(0, 0), image.size], fill=255)

    # Criar nova imagem com fundo transparente
    result = Image.new("RGBA", image.size, (0, 0, 0, 0))
    
    # Aplicar a máscara
    result.putalpha(mask)
    result.paste(image, (0, 0), mask)
    
    return result
    
async def obter_modo(user_id:int):
    
    async with AsyncSessionReze() as reze:
        result = await reze.execute(select(ModeOfTheBorderEditor).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        modo = userdb.mode
    
    return modo
    
def rgb_neon_glow(image: Image.Image, glow_strength: float = 2.0) -> Image.Image:
    """
    Cria efeito neon separando canais RGB
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Separa os canais de cor
    r, g, b = image.split()
    
    # Aplica efeito neon em cada canal
    def enhance_channel(channel, boost):
        channel = channel.point(lambda x: min(255, int(x * boost)))
        channel = channel.filter(ImageFilter.GaussianBlur(5))
        return channel
    
    r_glow = enhance_channel(r, glow_strength * 1.2)  # Vermelho mais forte
    g_glow = enhance_channel(g, glow_strength * 1.0)
    b_glow = enhance_channel(b, glow_strength * 1.1)  # Azul um pouco mais forte
    
    # Combina os canais com glow
    glow_image = Image.merge('RGB', (r_glow, g_glow, b_glow))
    
    # Mistura com original para manter detalhes
    result = Image.blend(image, glow_image, 0.3)
    
    # Aumenta saturação para efeito neon
    result = ImageEnhance.Color(result).enhance(1.5)
    result = ImageEnhance.Contrast(result).enhance(1.2)
    
    return result

def hard_glitch_modal(img: Image.Image, level: int = 5) -> Image.Image:
    """
    Aplica glitch pesado com nível customizável (1-10)
    Versão corrigida para evitar 'images do not match'
    """
    # Garante que estamos trabalhando com RGBA para consistência
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    width, height = img.size
    glitched = img.copy()
    
    # Ajusta parâmetros baseados no nível
    intensity = level / 10.0
    
    # 1. DESLOCAMENTOS DE FAIXAS HORIZONTAIS
    num_bands = int(5 + (15 * intensity))
    max_offset = int(10 + (40 * intensity))
    
    for _ in range(num_bands):
        y = random.randint(0, max(1, height - 10))
        h = random.randint(2, int(5 + (15 * intensity)))
        offset = random.randint(-max_offset, max_offset)
        
        # Garante que não sai dos limites
        if y + h > height:
            h = max(1, height - y)
        
        # Corta a faixa
        band = glitched.crop((0, y, width, y + h))
        
        # Aplica deslocamento com verificação de limites
        if offset >= 0:
            # Deslocamento para direita
            paste_x = min(offset, width - 1)
            glitched.paste(band, (paste_x, y))
        else:
            # Deslocamento para esquerda
            paste_x = 0
            # Corta a parte que vai além da borda esquerda
            crop_x = min(-offset, width - 1)
            cropped_band = band.crop((crop_x, 0, width, h))
            glitched.paste(cropped_band, (paste_x, y))
    
    # 2. DESALINHAMENTO RGB
    if level >= 2:
        try:
            # Separa os canais
            r, g, b, a = glitched.split()
            
            rgb_offset = int(2 + (8 * intensity))
            
            # Aplica offsets com verificação
            r_offset_x = random.randint(-rgb_offset, rgb_offset)
            g_offset_x = random.randint(-rgb_offset, rgb_offset) 
            b_offset_x = random.randint(-rgb_offset, rgb_offset)
            
            r = ImageChops.offset(r, r_offset_x, 0)
            g = ImageChops.offset(g, g_offset_x, 0)
            b = ImageChops.offset(b, b_offset_x, 0)
            
            # Recria a imagem com os canais desalinhados
            glitched = Image.merge("RGBA", (r, g, b, a))
        except Exception as e:
            print(f"Erro no RGB shift: {e}")
            # Continua sem RGB shift se houver erro
    
    # 3. AJUSTES DE COR
    if level >= 3:
        try:
            # Trabalha com cópia RGB para ajustes
            temp_rgb = glitched.convert('RGB')
            
            # Contraste
            contrast_factor = 1.0 + (1.5 * intensity)
            temp_rgb = ImageEnhance.Contrast(temp_rgb).enhance(contrast_factor)
            
            # Saturação (níveis mais altos)
            if level >= 6:
                color_factor = 1.0 + (2.0 * intensity)
                temp_rgb = ImageEnhance.Color(temp_rgb).enhance(color_factor)
            
            # Converte de volta mantendo alpha original
            temp_rgba = temp_rgb.convert('RGBA')
            r, g, b, _ = temp_rgba.split()
            _, _, _, a = glitched.split()
            glitched = Image.merge("RGBA", (r, g, b, a))
            
        except Exception as e:
            print(f"Erro nos ajustes de cor: {e}")
    
    # 4. RUÍDO DIGITAL
    noise_intensity = intensity ** 2
    num_noise_pixels = int(width * height * 0.002 * (level * 2))
    
    if num_noise_pixels > 0:
        pixels = glitched.load()
        for _ in range(num_noise_pixels):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            
            try:
                current_pixel = pixels[x, y]
                if level >= 8:
                    # Cor completamente aleatória
                    new_pixel = (
                        random.randint(0, 255),
                        random.randint(0, 255), 
                        random.randint(0, 255),
                        current_pixel[3] if len(current_pixel) > 3 else 255
                    )
                else:
                    # Variação sutil da cor atual
                    if len(current_pixel) == 4:
                        r, g, b, a = current_pixel
                        variation = random.randint(-50, 50)
                        new_pixel = (
                            max(0, min(255, r + variation)),
                            max(0, min(255, g + variation)),
                            max(0, min(255, b + variation)),
                            a
                        )
                    else:
                        # Fallback para RGB
                        r, g, b = current_pixel
                        variation = random.randint(-50, 50)
                        new_pixel = (
                            max(0, min(255, r + variation)),
                            max(0, min(255, g + variation)),
                            max(0, min(255, b + variation)),
                            255
                        )
                
                pixels[x, y] = new_pixel
            except:
                continue  # Ignora pixels problemáticos
    
    # 5. LINHAS DE CORRUÇÃO
    if level >= 5:
        num_corruption_lines = int(1 + (4 * intensity))
        
        for _ in range(num_corruption_lines):
            y = random.randint(0, height - 1)
            line_height = random.randint(1, int(1 + (3 * intensity)))
            
            for y_line in range(y, min(y + line_height, height)):
                color_shift = random.randint(-100, 100)
                for x in range(width):
                    try:
                        pixel = glitched.getpixel((x, y_line))
                        if len(pixel) == 4:
                            r, g, b, a = pixel
                            new_r = max(0, min(255, r + color_shift))
                            new_g = max(0, min(255, g - color_shift))
                            new_b = max(0, min(255, b + color_shift))
                            glitched.putpixel((x, y_line), (new_r, new_g, new_b, a))
                    except:
                        continue
    
    # 6. BLOCOS CORROMPIDOS
    if level >= 7:
        num_blocks = int(1 + (2 * intensity))
        
        for _ in range(num_blocks):
            block_size = random.randint(5, int(10 + (10 * intensity)))
            x = random.randint(0, max(1, width - block_size))
            y = random.randint(0, max(1, height - block_size))
            
            # Garante que o bloco não ultrapasse os limites
            actual_width = min(block_size, width - x)
            actual_height = min(block_size, height - y)
            
            if random.random() > 0.5:
                # Bloco de cor sólida
                block_color = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                    255
                )
                for bx in range(x, x + actual_width):
                    for by in range(y, y + actual_height):
                        try:
                            glitched.putpixel((bx, by), block_color)
                        except:
                            continue
            else:
                # Bloco de ruído
                for bx in range(x, x + actual_width):
                    for by in range(y, y + actual_height):
                        try:
                            noise_color = (
                                random.randint(0, 255),
                                random.randint(0, 255),
                                random.randint(0, 255),
                                255
                            )
                            glitched.putpixel((bx, by), noise_color)
                        except:
                            continue
    
    # 7. EFEITOS EXTRAS PARA NÍVEIS MÁXIMOS
    if level >= 9:
        num_inversions = int(2 * intensity)
        
        for _ in range(num_inversions):
            x = random.randint(0, max(1, width // 2))
            y = random.randint(0, max(1, height // 2))
            w = random.randint(10, width // 4)
            h = random.randint(10, height // 4)
            
            # Garante que não ultrapasse os limites
            actual_w = min(w, width - x)
            actual_h = min(h, height - y)
            
            if actual_w > 0 and actual_h > 0:
                try:
                    area = glitched.crop((x, y, x + actual_w, y + actual_h))
                    # Inverte apenas RGB, mantém alpha
                    inverted_rgb = ImageChops.invert(area.convert('RGB'))
                    inverted_rgba = inverted_rgb.convert('RGBA')
                    
                    # Pega o canal alpha original
                    _, _, _, original_alpha = area.split()
                    inverted_rgba.putalpha(original_alpha)
                    
                    glitched.paste(inverted_rgba, (x, y))
                except Exception as e:
                    print(f"Erro na inversão: {e}")
                    continue
    
    return glitched

# Função auxiliar para demonstrar os diferentes níveis
def create_glitch_preview(image: Image.Image) -> Image.Image:
    """Cria uma imagem com preview de todos os níveis de glitch"""
    width, height = image.size
    preview_width = width * 2
    preview_height = height * 5  # 2 colunas x 5 linhas
    
    preview = Image.new('RGBA', (preview_width, preview_height), (0, 0, 0, 255))
    
    for level in range(1, 11):
        glitched = hard_glitch(image, level)
        
        # Calcula posição na grade
        col = (level - 1) % 2
        row = (level - 1) // 2
        
        x = col * width
        y = row * height
        
        preview.paste(glitched, (x, y))
    
    return preview

def hard_glitch_effect(image: Image.Image, intensity: int = 5, rgb_shift: bool = True, 
                      slice_shift: bool = True, distortion: bool = True) -> Image.Image:
    """
    Aplica efeito glitch pesado e customizável
    intensity: 1-10 (controla força dos efeitos)
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    width, height = image.size
    
    # Converte para array para manipulação
    img_array = np.array(image)
    
    # Aplica diferentes tipos de glitch baseado na intensidade
    if rgb_shift:
        img_array = apply_rgb_shift(img_array, intensity)
    
    if slice_shift:
        img_array = apply_slice_shift(img_array, intensity)
    
    if distortion:
        img_array = apply_distortion(img_array, intensity)
    
    # Adiciona ruído digital
    img_array = add_digital_noise(img_array, intensity)
    
    # Converte de volta para Image
    result = Image.fromarray(img_array)
    
    return result

def apply_rgb_shift(img_array: np.ndarray, intensity: int) -> np.ndarray:
    """Desloca canais RGB individualmente"""
    height, width, _ = img_array.shape
    shift_amount = intensity * 2
    
    # Cria cópias dos canais
    r_channel = img_array[:, :, 0].copy()
    g_channel = img_array[:, :, 1].copy() 
    b_channel = img_array[:, :, 2].copy()
    
    # Aplica deslocamentos aleatórios
    r_shift = random.randint(-shift_amount, shift_amount)
    g_shift = random.randint(-shift_amount, shift_amount)
    b_shift = random.randint(-shift_amount, shift_amount)
    
    # Desloca canais
    if r_shift > 0:
        r_channel[:, r_shift:] = r_channel[:, :-r_shift]
    elif r_shift < 0:
        r_channel[:, :r_shift] = r_channel[:, -r_shift:]
    
    if g_shift > 0:
        g_channel[g_shift:, :] = g_channel[:-g_shift, :]
    elif g_shift < 0:
        g_channel[:g_shift, :] = g_channel[-g_shift:, :]
    
    # Combina canais deslocados
    result = np.stack([r_channel, g_channel, b_channel], axis=2)
    
    return result

def apply_slice_shift(img_array: np.ndarray, intensity: int) -> np.ndarray:
    """Desloca fatias horizontais da imagem"""
    height, width, _ = img_array.shape
    result = img_array.copy()
    
    # Número de fatias baseado na intensidade
    num_slices = intensity * 3
    
    for _ in range(num_slices):
        # Seleciona uma fatia aleatória
        slice_height = random.randint(5, 20)
        slice_y = random.randint(0, height - slice_height)
        
        # Deslocamento horizontal
        shift_x = random.randint(-intensity * 3, intensity * 3)
        
        if shift_x > 0:
            # Desloca para direita
            result[slice_y:slice_y+slice_height, shift_x:] = \
                img_array[slice_y:slice_y+slice_height, :-shift_x]
        elif shift_x < 0:
            # Desloca para esquerda  
            result[slice_y:slice_y+slice_height, :shift_x] = \
                img_array[slice_y:slice_y+slice_height, -shift_x:]
    
    return result

def apply_distortion(img_array: np.ndarray, intensity: int) -> np.ndarray:
    """Aplica distorção wave-like"""
    height, width, _ = img_array.shape
    result = img_array.copy()
    
    # Cria padrão de onda
    for y in range(height):
        wave = int(math.sin(y / 20) * intensity)
        if wave > 0:
            result[y, wave:] = img_array[y, :-wave]
        elif wave < 0:
            result[y, :wave] = img_array[y, -wave:]
    
    return result

def add_digital_noise(img_array: np.ndarray, intensity: int) -> np.ndarray:
    """Adiciona ruído digital e artefatos de compressão"""
    height, width, _ = img_array.shape
    result = img_array.copy()
    
    # Adiciona linhas de cor aleatórias
    for _ in range(intensity * 2):
        y = random.randint(0, height - 1)
        color = [random.randint(0, 255) for _ in range(3)]
        result[y, :] = color
    
    # Adiciona blocos corrompidos
    for _ in range(intensity):
        block_size = random.randint(5, 15)
        x = random.randint(0, width - block_size)
        y = random.randint(0, height - block_size)
        
        # Preenche com cor sólida ou ruído
        if random.random() > 0.5:
            color = [random.randint(0, 255) for _ in range(3)]
            result[y:y+block_size, x:x+block_size] = color
        else:
            noise = np.random.randint(0, 255, (block_size, block_size, 3))
            result[y:y+block_size, x:x+block_size] = noise
    
    return result

def vhs_effect(image: Image.Image, scan_lines: bool = True, color_bleed: bool = True) -> Image.Image:
    """
    Aplica efeito VHS retro
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 1. Reduz saturação e contraste
    from PIL import ImageEnhance
    image = ImageEnhance.Color(image).enhance(0.8)
    image = ImageEnhance.Contrast(image).enhance(1.2)
    
    # 2. Adiciona linhas de scan (opcional)
    if scan_lines:
        image = add_scan_lines(image)
    
    # 3. Adiciona vazamento de cor (opcional)
    if color_bleed:
        image = add_color_bleed(image)
    
    # 4. Adiciona ruído leve
    image = image.filter(ImageFilter.GaussianBlur(0.3))
    
    return image

def add_scan_lines(image: Image.Image) -> Image.Image:
    """Adiciona linhas de scan como em TVs antigas"""
    width, height = image.size
    result = image.copy()
    draw = ImageDraw.Draw(result)
    
    # Cria linhas escuras horizontais
    for y in range(0, height, 4):
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, 80), width=1)
    
    # Adiciona linhas brilhantes ocasionais
    for _ in range(3):
        y = random.randint(0, height - 1)
        draw.line([(0, y), (width, y)], fill=(255, 255, 255, 30), width=1)
    
    return result

def add_color_bleed(image: Image.Image) -> Image.Image:
    """Adiciona efeito de vazamento de cor"""
    width, height = image.size
    
    # Cria cópias deslocadas para cada canal de cor
    r, g, b = image.split()
    
    # Desloca o canal vermelho
    r_shifted = Image.new('L', (width, height), 0)
    r_shifted.paste(r, (2, 0))
    
    # Desloca o canal azul
    b_shifted = Image.new('L', (width, height), 0)
    b_shifted.paste(b, (-2, 0))
    
    # Combina os canais
    result = Image.merge('RGB', (r_shifted, g, b_shifted))
    
    return result

async def get_avatar(url:str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as response:
            return io.BytesIO(await response.read())
        
def add_vhs_glitch(frame):
    """Aplica glitch VHS simples na imagem"""
    width, height = frame.size
    frame = frame.copy()
    
    # Deslocamento horizontal aleatório de linhas
    for _ in range(random.randint(5, 15)):
        y = random.randint(0, height-1)
        h = random.randint(1, 5)
        offset = random.randint(-10, 10)
        if y+h < height:
            band = frame.crop((0, y, width, y+h))
            frame.paste(band, (offset, y))
    
    # Pequeno deslocamento de cores RGB usando ImageChops.offset
    r, g, b = frame.split()
    r = ImageChops.offset(r, random.randint(-3,3), 0)
    g = ImageChops.offset(g, random.randint(-3,3), 0)
    b = ImageChops.offset(b, random.randint(-3,3), 0)
    frame = Image.merge("RGB", (r, g, b))
    
    return frame

def add_play_icon(frame):
    """Adiciona o play ▶️ no canto inferior direito"""
    draw = ImageDraw.Draw(frame)
    font_size = frame.width // 6
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    text = "▶️"

    # Usa textbbox para medir tamanho do texto
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = frame.width - text_width - 10
    y = frame.height - text_height - 10
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    return frame

# ========== EFEITOS DE GLITCH ==========
def soft_glitch(img):
    """Aplica um glitch suave (RGB shift e leves distorções)"""
    img = img.convert("RGB")
    width, height = img.size
    glitched = img.copy()

    # separa canais de cor
    r, g, b = glitched.split()
    r = ImageChops.offset(r, random.randint(-3, 3), 0)
    b = ImageChops.offset(b, random.randint(3, 6), 0)
    glitched = Image.merge("RGB", (r, g, b))

    # adiciona pequenas faixas horizontais
    for _ in range(random.randint(5, 10)):
        y = random.randint(0, height - 5)
        h = random.randint(2, 5)
        offset = random.randint(-10, 10)
        band = glitched.crop((0, y, width, y + h))
        glitched.paste(band, (offset, y))

    # leve aumento de contraste e saturação
    glitched = ImageEnhance.Contrast(glitched).enhance(1.3)
    glitched = ImageEnhance.Color(glitched).enhance(1.2)
    return glitched

def hard_glitch(img):
    """Aplica um glitch pesado (cortes, distorção e saturação extrema)"""
    img = img.convert("RGB")
    width, height = img.size
    glitched = img.copy()

    # deslocamentos grandes e faixas
    for _ in range(random.randint(10, 20)):
        y = random.randint(0, height - 5)
        h = random.randint(5, 20)
        offset = random.randint(-50, 50)
        band = glitched.crop((0, y, width, y + h))
        glitched.paste(band, (offset, y))

    # RGB severamente desalinhado
    r, g, b = glitched.split()
    r = ImageChops.offset(r, random.randint(-10, 10), 0)
    g = ImageChops.offset(g, random.randint(-10, 10), 0)
    b = ImageChops.offset(b, random.randint(-10, 10), 0)
    glitched = Image.merge("RGB", (r, g, b))

    # saturação e contraste altos
    glitched = ImageEnhance.Contrast(glitched).enhance(2.0)
    glitched = ImageEnhance.Color(glitched).enhance(2.5)

    # ruído randômico
    pixels = glitched.load()
    for _ in range(int(width * height * 0.01)):  # 1% dos pixels
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        pixels[x, y] = tuple(random.randint(0, 255) for _ in range(3))

    return glitched

def static_effect(image: Image.Image, intensity: float = 0.3) -> Image.Image:
    """
    Aplica efeito de estática/ruído de TV
    intensity: 0.1 (leve) a 0.8 (forte)
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Converte para array numpy
    img_array = np.array(image)
    height, width, channels = img_array.shape
    
    # Gera ruído aleatório
    noise = np.random.randint(0, 255, (height, width, channels), dtype=np.uint8)
    
    # Mistura o ruído com a imagem original
    result_array = img_array * (1 - intensity) + noise * intensity
    result_array = np.clip(result_array, 0, 255).astype(np.uint8)
    
    # Converte de volta para Image
    return Image.fromarray(result_array)

class ModalForSettingsBorderSolidGradient(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Configure a borda Gradiente.")

        self.inputtext1 = discord.ui.TextInput(label="Escolha a cor 1.", placeholder="Ex: #000000", max_length=10)
        self.inputtext2 = discord.ui.TextInput(label="Escolha a cor 2.", placeholder="Ex: #000000", max_length=10)
        self.inputtext3 = discord.ui.TextInput(label="Escolha a direção das cores.", placeholder="Ex: Horizontal/Vertical", max_length=20)
        self.inputtext4 = discord.ui.TextInput(label="Escolha o tamanho da borda.", placeholder="Ex: 2", max_length=2)
        self.add_item(self.inputtext1)
        self.add_item(self.inputtext2)
        self.add_item(self.inputtext3)
        self.add_item(self.inputtext4)

    async def on_submit(self, interaction:discord.Interaction):
        
        try:
            with Image.open(f"image_editor_path/{interaction.user.id}.png").convert("RGBA") as img:
                
                color1 = self.inputtext1.value
                color2 = self.inputtext2.value
                direction = self.inputtext3.value
                size = int(self.inputtext4.value)
                
                img = await circule_image(img)
                final_image = add_simple_gradient_border(
                    image=img,
                    border_width=size,
                    start_color=color1,
                    end_color=color2,
                    direction=direction
                    ).save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
                    
        except Exception as e:
            return await interaction.response.send_message(f"❌ Ocorreu um erro ao editar imagem!\n{e}")
        
        await interaction.response.send_message("✅ Imagem editada com sucesso!")

class ModalForSettingsBorderNeonGradient(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Configure a borda Neon.")
        
        self.inputtext1 = discord.ui.TextInput(label="Escolha a cor 1.", placeholder="Ex: #000000", max_length=10)
        self.inputtext4 = discord.ui.TextInput(label="Escolha o tamanho da borda.", placeholder="Ex: 2", max_length=3)
        self.itex = discord.ui.TextInput(label="Escolha a intensidade do Glown Neon.", placeholder="Ex: 10", max_length=3)
        self.add_item(self.inputtext1)
        self.add_item(self.inputtext4)
        self.add_item(self.itex)
        
    async def on_submit(self, interaction: discord.Interaction):
        # 🔴 NÃO FAÇA NADA ANTES DO DEFER
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Todo o processamento DEPOIS do defer
            with Image.open(f"image_editor_path/{interaction.user.id}.png").convert("RGBA") as img:
                
                color1 = self.inputtext1.value
                size = int(self.inputtext4.value)
                intensity = int(self.itex.value)
                
                img = await circule_image(img)
                img_final = await add_circular_glow_neon_async(
                    image=img, 
                    glow_color=color1, 
                    border_width=size, 
                    glow_intensity=intensity
                )
                img_final.save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
                                
            await interaction.followup.send("✅ Imagem editada com sucesso!", ephemeral=True)
            
        except Exception as e:
            print(f"Erro no processamento da imagem: {e}")
            await interaction.followup.send(f"❌ Erro ao processar imagem: {str(e)}", ephemeral=True)

class ModalForSettingsBorderSolideNoGradient(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Configure a borda.")
        
        self.inputtext1 = discord.ui.TextInput(label="Escolha a cor.", placeholder="Ex: #000000", max_length=10)
        self.add_item(self.inputtext1)

    async def on_submit(self, interaction:discord.Interaction):
        
        await interaction.response.send_message("")

        #=============================================
        #CONFIGURAÇÕES DO EDITOR DE BORDAS DO BOT REZE
        #=============================================
            
class ButtonsForOpenConfigsAboutBorder(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(self.ButtonGradientSolidBorder())
        self.add_item(self.ButtonGradientNeonGlownBorder())
        # self.add_item(self.ButtonBorder())
        self.add_item(self.ButtonOpenForHelp())
        
    class ButtonGradientSolidBorder(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Configurar Borda Gradiente.", style=discord.ButtonStyle.blurple, custom_id="btn_gradient_border", emoji="🎨")
            
        async def callback(self, interaction:discord.Interaction):
            await interaction.response.send_modal(ModalForSettingsBorderSolidGradient())

    class ButtonBorder(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Configurar Borda.", style=discord.ButtonStyle.grey, custom_id="btn_border", emoji="💿")
            
        async def callback(self, interaction:discord.Interaction):
            await interaction.response.send_modal(ModalForSettingsBorderSolideNoGradient())

    class ButtonGradientNeonGlownBorder(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Configurar Borda Neon Glown.", style=discord.ButtonStyle.green, custom_id="btn_neon_border", emoji="🔮")
            
        async def callback(self, interaction:discord.Interaction):
            await interaction.response.send_modal(ModalForSettingsBorderNeonGradient())
            
    class ButtonOpenForHelp(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Open Help", style=discord.ButtonStyle.red, custom_id="btn_help_border", emoji="✅")
            
        async def callback(self, interaction:discord.Interaction):
            
            embed = discord.Embed(
                title="Informações.",
                description="Aqui você tem um guia básico.",
                color=0x23046b,
                timestamp=discord.utils.utcnow()
            ).set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url).set_thumbnail(url=interaction.user.avatar.url)
            
            embed.add_field(name="Cores:", value="Você sempre deve colocar a cor no format hexadecimal, nunca coloque em outro formato.", inline=True)
            embed.add_field(name="Efeito Neon Glow:", value="Em fase testes, pode não funcionar perfeitamente.", inline=True)
            
            await interaction.response.send_message(embed=embed)

class ButtonAndViewImageEditor(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.author_id = ctx_author_id
        
    def make_circle(self, img: Image.Image) -> Image.Image:
        # Garante que tenha canal alpha (transparência)
        img = img.convert("RGBA")
        width, height = img.size

        # Cria máscara circular (preto e branco)
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, height), fill=255)

        # Aplica a máscara na imagem
        circular = Image.new("RGBA", (width, height))
        circular.paste(img, (0, 0), mask=mask)
        return circular
    
    def frimg(self, user_id:int, mode:str = None):
        
        if mode is None:
            path = f"image_editor_path/{user_id}.png"

        if mode == "imagem":
            path = f"image_editor_path/{user_id}.png"
        elif mode == "gif":
            path = f"image_editor_path/{user_id}.gif"
        else:
            path = f"image_editor_path/{user_id}.png"        
        
        return path
        
    class ModalRedimensionarImage(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="Redimensione/Melhore a resolução.")
            self.sz1 = discord.ui.TextInput(
                label="Largura", placeholder="Ex: 200", max_length=5, required=True
            )
            self.sz2 = discord.ui.TextInput(
                label="Altura", placeholder="Ex: 200", max_length=5, required=True
            )

            self.add_item(self.sz1)
            self.add_item(self.sz2)
            
        async def on_submit(self, interaction:discord.Interaction):

            try:
                sz1 = int(self.sz1.value)
                sz2 = int(self.sz2.value)
            except:
                return interaction.response.send_message("❌ Ocorreu um erro ao carregar as medidas definidas!")
            
            if sz1 > 5000:
                return interaction.response.send_message("❌ Largura muito grande!")
            
            if sz2 > 5000:
                return interaction.response.send_message("❌ Altura muito grande!")

            try:
                img_path = f"image_editor_path/{interaction.user.id}.png"
                img = Image.open(img_path).convert("RGBA").resize((sz1, sz2))
            except:
                return interaction.response.send_message("❌ Ocorreu um erro ao tentar carregar sua imagem! Tem certeza que enviou alguma?")
            
            img.save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
            await interaction.response.send_message("✅ Imagem editada e salva com sucesso!")
            
    class ViewForEffectsOfImageEditorOfTheKeith(discord.ui.View):
        def __init__(self, interact_author_id):
            super().__init__(timeout=240)
            self.author_id = interact_author_id

        def frimg(self, user_id:int, mode:str = None):
            
            if mode is None:
                path = f"image_editor_path/{user_id}.png"

            if mode == "imagem":
                path = f"image_editor_path/{user_id}.png"
            elif mode == "gif":
                path = f"image_editor_path/{user_id}.gif"
            else:
                path = f"image_editor_path/{user_id}.png"        
            
            return path

        class ModalForEffectBlur(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Escolha o nível do efeito Blur.")
        
                self.effect_blur = discord.ui.TextInput(label="Coloque o nível do Blur:", placeholder="Ex: Min: 1/Max: 10", max_length=2, min_length=1, required=True)
                self.add_item(self.effect_blur)
                
            async def on_submit(self, interaction:discord.Interaction):

                try:                
                    with Image.open(f"image_editor_path/{interaction.user.id}.png") as img:
                        img = img.filter(ImageFilter.GaussianBlur(int(self.effect_blur.value)))
                        img.save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
                except:
                    return interaction.response.send_message("❌ Ocorreu um erro ao editar a imagem! Tem certeza que enviou alguma?", ephemeral=True)
                
                await interaction.response.send_message("✅ Imagem editada com sucesso!", ephemeral=True)
                
        class ModalForPixelArtSettings(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Escolha os pixels da pixel art", timeout=300)
                
                self.input1 = discord.ui.TextInput(
                    label="Coloque aqui a quantidade de pixel (Largura)",
                    placeholder="Ex: Min: 32/Max: 256",
                    required=True,
                    min_length=2,
                    max_length=3
                )
                self.input2 = discord.ui.TextInput(
                    label="Coloque aqui a quantidade de pixel (Altura)", 
                    placeholder="Ex: Min: 32/Max: 256",
                    required=True,
                    min_length=2,
                    max_length=3
                )
                self.add_item(self.input1)
                self.add_item(self.input2)
                
            async def on_submit(self, interaction: discord.Interaction):
                try:
                    # Validar e converter valores
                    width = int(self.input1.value)
                    height = int(self.input2.value)
                    
                    # Validar limites
                    if not (32 <= width <= 256):
                        await interaction.response.send_message("❌ Largura deve estar entre 32 e 256", ephemeral=True)
                        return
                        
                    if not (32 <= height <= 256):
                        await interaction.response.send_message("❌ Altura deve estar entre 32 e 256", ephemeral=True)
                        return
                    
                    # Abrir imagem corretamente
                    image_path = f"image_editor_path/{interaction.user.id}.png"
                    
                    with Image.open(image_path) as img:
                        # Converter para RGB se necessário
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Redimensionar para o tamanho pixel art (pequeno)
                        small = img.resize((width, height), Image.Resampling.NEAREST)
                        
                        # Aplicar paleta CGA (opcional - remove se quiser só o redimensionamento)
                        cga_palette = [
                            (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
                            (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
                            (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
                            (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)
                        ]
                        
                        # Aplicar paleta limitada
                        small_paletted = small.convert("P", palette=Image.ADAPTIVE, colors=16)
                        
                        # Criar imagem final redimensionada de volta (opcional)
                        # Se quiser manter pequeno, use apenas small_paletted
                        final_size = (img.width, img.height)  # ou mantenha (width, height) para imagem pequena
                        final_img = small_paletted.resize(final_size, Image.Resampling.NEAREST)
                        
                        # Salvar
                        final_img.save(image_path, format="PNG")
                        
                    await interaction.response.send_message("✅ Imagem editada com sucesso!", ephemeral=True)
                    
                except ValueError:
                    await interaction.response.send_message("❌ Por favor, digite números válidos!", ephemeral=True)
                except FileNotFoundError:
                    await interaction.response.send_message("❌ Imagem não encontrada! Envie uma imagem primeiro.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Erro ao processar imagem: {str(e)}", ephemeral=True)
                
        class ModalForStaticEffect(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Adicionar efeito estática", timeout=300)  # Added timeout
                self.input1 = discord.ui.TextInput(
                    label="Escolha a intensidade do efeito de estática",
                    placeholder="Ex: Min: 0.1/Max: 0.8",
                    required=True,
                    min_length=1,
                    max_length=4
                )
                self.add_item(self.input1)
            
            async def on_submit(self, interaction: discord.Interaction):
                try:
                    # Convert to float with error handling
                    intensity = float(self.input1.value)
                    
                    # Validate range
                    if intensity > 0.8:
                        await interaction.response.send_message("❌ Não coloque um valor acima de 0.8", ephemeral=True)
                        return
                    if intensity < 0.1:
                        await interaction.response.send_message("❌ Não coloque um valor abaixo de 0.1", ephemeral=True)
                        return
                    
                    # Process image
                    try:
                        with Image.open(f"image_editor_path/{interaction.user.id}.png") as img:
                            result = static_effect(image=img, intensity=intensity)
                            result.save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
                    except FileNotFoundError:
                        await interaction.response.send_message("❌ Imagem não encontrada! Envie uma imagem primeiro.", ephemeral=True)
                        return
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Erro ao processar imagem: {str(e)}", ephemeral=True)
                        return
                    
                    await interaction.response.send_message("✅ Imagem editada com sucesso!", ephemeral=True)
                    
                except ValueError:
                    await interaction.response.send_message("❌ Por favor, digite um número válido (ex: 0.5)", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Erro inesperado: {str(e)}", ephemeral=True)
            
            async def on_error(self, interaction: discord.Interaction, error: Exception):
                await interaction.response.send_message("❌ Ocorreu um erro inesperado!", ephemeral=True)
                # Log the error for debugging
                print(f"Modal error: {error}")
                
        class ModalForHardGlitchEffect(discord.ui.Modal):
            def __init__(self, *, title = ..., timeout = None, custom_id = ...):
                super().__init__(title="Aplique o efeito Hard Glitch")
                self.input1 = discord.ui.TextInput(label="Escolha a intensidade do Glitch", placeholder="Ex: Min: 1/Max: 10")
                self.add_item(self.input1)
                
            async def on_submit(self, interaction:discord.Interaction):
                try:
                    # Valida intensidade
                    intensity = int(self.input1.value)
                    intensity = max(1, min(10, intensity))
                    
                    with Image.open(f"image_editor_path/{interaction.user.id}.png") as img:
                        result = hard_glitch_modal(img=img, level=intensity)
                        result.save(f"image_editor_path/{interaction.user.id}.png")
                except Exception as e:
                    return await interaction.response.send_message(f"❌ Ocorreu um erro ao editar imagem! Tem certeza que enviou alguma?\n{e}")
                
                await interaction.response.send_message("✅ Imagem editada com sucesso!")
                        
        @discord.ui.button(label="Efeito Blur", style=discord.ButtonStyle.grey, custom_id="blur_effect")
        async def effect_blur_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)

            await interaction.response.send_modal(self.ModalForEffectBlur())
            
        @discord.ui.button(label="Efeito Preto e Branco", style=discord.ButtonStyle.grey, custom_id="bw_btn")
        async def bw_functionbtn(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)

            try:            
                with Image.open(self.frimg(user_id=interaction.user.id, mode="imagem")) as img:
                    bw = img.convert('L')
                    bw.save(self.frimg(interaction.user.id), "imagem", format="PNG")
            except:
                return await interaction.response.send_message("❌ Ocorreu um erro ao editar imagem! Tem certeza que enviou alguma?", ephemeral=True)
                
            await interaction.response.send_message("✅ Imagem editada com sucesso!", ephemeral=True)
            
        @discord.ui.button(label="Efeito LGBTQIAPN+", style=discord.ButtonStyle.grey, custom_id="lgbtqiapn_btn")
        async def lgbtqiapn_effect(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            
            try:
                with Image.open(self.frimg(user_id=interaction.user.id, mode="imagem")) as img:
                    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(overlay)
                    
                    colors = [
                        (255, 0, 0, 100),    # Vermelho
                        (255, 165, 0, 100),  # Laranja
                        (255, 255, 0, 100),  # Amarelo
                        (0, 255, 0, 100),    # Verde
                        (0, 0, 255, 100),    # Azul
                        (75, 0, 130, 100)    # Roxo
                    ]
                    
                    stripe_height = img.height // len(colors)
                    for i, color in enumerate(colors):
                        y0 = i * stripe_height
                        y1 = (i + 1) * stripe_height
                        draw.rectangle([0, y0, img.width, y1], fill=color)
                        
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                        
                    result = Image.alpha_composite(img, overlay)
                    result.save(self.frimg(interaction.user.id, "imagem"), format="PNG")
            except:
                return await interaction.response.send_message("❌ Ocorreu um erro ao editar imagem! Tem certeza que enviou alguma?", ephemeral=True)
        
            await interaction.response.send_message("✅ Imagem editada com sucesso!", ephemeral=True)
            
        @discord.ui.button(label="Espelhar imagem", style=discord.ButtonStyle.grey, custom_id="mirror_edit_btn")
        async def mirror_img_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            
            try:
                with Image.open(self.frimg(interaction.user.id, "Imagem")) as img:
                    mirrored = ImageOps.mirror(img)
                    mirrored.save(self.frimg(interaction.user.id, "imagem"), format="PNG")
            except:
                return await interaction.response.send_message("❌ Ocorreu um erro ao editar imagem! Tem certeza que enviou alguma?", ephemeral=True)
            
            await interaction.response.send_message("✅ Imagem editada com sucesso!", ephemeral=True)
            
        @discord.ui.button(label="Inverter Cores", style=discord.ButtonStyle.grey, custom_id="invert_colors_btn", row=2)
        async def invert_colors_btn_f(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            
            try:
                with Image.open(self.frimg(interaction.user.id, "imagem")) as img:                    
                    inverted = ImageOps.invert(img)
                    inverted.save(self.frimg(interaction.user.id, "imagem"), format="PNG")
            except Exception as e:
                return await interaction.response.send_message(f"❌ Ocorreu um erro ao editar imagem! Tem certeza que enviou alguma?\n\n{e}", ephemeral=True)
            
            await interaction.response.send_message("✅ Imagem editada com sucesso!", ephemeral=True)
            
        @discord.ui.button(label="Pixel Art", style=discord.ButtonStyle.grey, custom_id="pixel_art_btn", row=2)
        async def pixel_art_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            
            await interaction.response.send_modal(self.ModalForPixelArtSettings())                    
        
        @discord.ui.button(label="Efeito de estática", style=discord.ButtonStyle.grey, custom_id="static_btn", row=2)
        async def static_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            
            await interaction.response.send_modal(self.ModalForStaticEffect())
            
        @discord.ui.button(label="Efeito de VHS", style=discord.ButtonStyle.grey, custom_id="VHS_btn", row=2)
        async def VHS_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)

            try:            
                with Image.open(self.frimg(interaction.user.id, "imagem")) as img:
                    result = vhs_effect(img)
                    result.save(self.frimg(interaction.user.id, "imagem"), format="PNG")
            except:
                return await interaction.response.send_message("❌ Ocorreu um erro ao editar imagem! Tem certeza que enviou alguma?")
            
            await interaction.response.send_message("✅ Imagem editada com sucesso!") 
        
        @discord.ui.button(label="Efeito Glitch", style=discord.ButtonStyle.grey, custom_id="hard_glitch_btn", row=2)
        async def hard_glitch_btn_function_c(self, interaction:discord.Interaction, button:discord.ui.Button):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            
            await interaction.response.send_modal(self.ModalForHardGlitchEffect())
        
    @discord.ui.button(label="Enviar Imagem", style=discord.ButtonStyle.green, custom_id="enviar_imagem_button", row=1)
    async def enviar_imagem_function(self, interaction: discord.Interaction, button: discord.ui.Button):

        # Apenas o autor pode usar o botão
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message(
                "❌ Somente o autor do comando pode clicar nesses botões!",
                ephemeral=True
            )

        # Resposta inicial para evitar timeout
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            "📸 Você tem **60 segundos** para enviar **qualquer imagem**, exceto GIFs ou vídeos!",
            ephemeral=True
        )

        # Função de verificação da mensagem enviada
        def check(msg: discord.Message):
            if msg.author != interaction.user or msg.channel != interaction.channel:
                return False
            if not msg.attachments:
                return False

            att = msg.attachments[0]
            ctype = (att.content_type or "").lower()
            filename = att.filename.lower()

            # Extensões e tipos bloqueados (vídeos e GIFs)
            blocked_ext = (".gif", ".mp4", ".mov", ".avi", ".webm", ".mkv")
            blocked_types = ("video/",)

            # Bloquear vídeos e GIFs
            if filename.endswith(blocked_ext):
                return False
            if any(ctype.startswith(b) for b in blocked_types):
                return False

            # Aceitar imagens (JPG, PNG, WEBP, etc.)
            return ctype.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp"))

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=60.0)
            attachment = msg.attachments[0]

            # Garante que a pasta exista
            os.makedirs("image_editor_path", exist_ok=True)

            ext = attachment.filename.split(".")[-1].lower()
            file_path = f"image_editor_path/{interaction.user.id}.png"
            await attachment.save(file_path)

            await interaction.followup.send(
                f"✅ Arquivo de imagem recebido e salvo como `{interaction.user.id}.{ext}`!",
                ephemeral=True
            )

        except asyncio.TimeoutError:
            await interaction.followup.send(
                "⏰ Tempo esgotado! Nenhum arquivo de imagem válido foi enviado.",
                ephemeral=True
            )
            
    @discord.ui.button(label="Circular Imagem.", style=discord.ButtonStyle.grey, custom_id="circule_image_elipse", row=2)
    async def circular_imagem_bu(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        try:
            img_path = f"image_editor_path/{interaction.user.id}.png"
            img = Image.open(img_path).convert("RGBA")
        except:
            return await interaction.response.send_message("❌ Imagem não foi encontrada, tem certeza que enviou alguma imagem?", ephemeral=True)
        
        final_img = self.make_circle(img=img)
        
        final_img.save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
        
        await interaction.response.send_message("✅ Imagem editada com sucesso, clique no botão `Ver Imagem` para verificar o resultado.", ephemeral=True)
        
    @discord.ui.button(label="Abrir Lista de Efeitos.", style=discord.ButtonStyle.grey, custom_id="effects_list_button", row=2)
    async def open_effects_list(self, interaction:discord.Interaction, button:discord.ui.button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        embed = discord.Embed(
            title="🈹 Effects List do Keith.",
            description="🔮 Aqui você pode escolher quais efeitos aplicar na sua imagem.",
            color=discord.Color.dark_purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {interaction.user.name}", icon_url=interaction.user.avatar.url)
        
        await interaction.response.send_message(embed=embed, view=self.ViewForEffectsOfImageEditorOfTheKeith(interaction.user.id))
        
    @discord.ui.button(label="Editor de Bordas.", style=discord.ButtonStyle.grey, custom_id="border_editor_btn", row=2)
    async def border_editor_open_class_btn_decorator_n(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        embed = discord.Embed(
            title="🈳 Editor de Borda.",
            description="Aqui você pode escolher as configurações da borda.",
            color=0x23046b,
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url).set_thumbnail(url=interaction.user.avatar.url)
        
        await interaction.response.send_message(embed=embed, view=ButtonsForOpenConfigsAboutBorder())
        
    @discord.ui.button(label="Redimensionar Imagem.", style=discord.ButtonStyle.grey, custom_id="contorn_image_id", row=2)
    async def contorn_in_image(self, interaction:discord.Interaction, button:discord.ui.Button):
    
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        await interaction.response.send_modal(self.ModalRedimensionarImage())
        
    @discord.ui.button(label="Converter Formato.", style=discord.ButtonStyle.grey, custom_id="cvft_btn", row=3)
    async def format_convert(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        view_convert = discord.ui.View()
        button_1_cvft = discord.ui.Button(label="Open Configs", style=discord.ButtonStyle.green, custom_id="open_configs")
        
        class ModalForFormatConvert(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Escolha o formato em que a imagem vai estar.")
                
                self.inputtext = discord.ui.TextInput(label="Escolha o Formato.", max_length=5, required=True, min_length=1)
                self.add_item(self.inputtext)
                
            async def on_submit(self, interaction:discord.Interaction):
                
                try:                
                    with Image.open(f"image_editor_path/{interaction.user.id}.png") as img:
                        prefix_file = self.inputtext.value
                        buffer = io.BytesIO()
                        img.save(buffer, format=f"{prefix_file.upper()}")
                        buffer.seek(0)
                        
                        img_filed = discord.File(buffer, filename=f"converted.{prefix_file.lower()}")

                        embed = discord.Embed(
                            title=f"Imagem convertida para o formato: .{prefix_file.upper()}",
                            description=f"Imagem conertida com sucesso, {interaction.user.display_name}!",
                            color=discord.Color.purple(),
                            timestamp=discord.utils.utcnow()
                        ).set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url).set_image(url=f"attachment://converted.{prefix_file.lower()}")

                        await interaction.response.send_message(file=img_filed, embed=embed, ephemeral=True)
                        
                except Exception as e:
                    return await interaction.response.send_message(f"❌ Ocorreu um erro ao editar sua imagem!\n{e}", ephemeral=True)
        
        async def callback_configs(interaction:discord.Interaction):
            
            if self.author_id != interaction.user.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)

            await interaction.response.send_modal(ModalForFormatConvert())
            
        button_1_cvft.callback = callback_configs
        view_convert.add_item(button_1_cvft)
        
        formats_list_embed = discord.Embed(
            title="🖼️ Formatos Suportados pelo Pillow (PIL)",
            description="Lista completa dos formatos de imagem..",
            color=0x4B8BBE  # Azul estilo Python 😄
        )

        formats_list_embed.add_field(
            name="✅ **Leitura e Escrita**",
            value=(
                "• **BMP**\n"
                "• **JPEG / JPG**\n"
                "• **PNG**\n"
                "• **PPM / PGM / PNM**\n"
                "• **TIFF**\n"
                "• **AVIF**\n"
                "• **QOI**\n"
                "• **MPO**\n"
                "• **IM**\n"
                "• **PCX**\n"
                "• **SGI**\n"
                "• **SPIDER**\n"
                "• **BLP**"
            ),
            inline=False
        )

        formats_list_embed.set_footer(
            text=f"{interaction.user.name}",
            icon_url=interaction.user.avatar.url
        )
            
        await interaction.response.send_message(embed=formats_list_embed, view=view_convert)
        
    @discord.ui.button(label="Remover Fundo.", style=discord.ButtonStyle.grey, custom_id="rembg_btn", row=3)
    async def remover_background_api(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        await interaction.response.send_message("Sua imagem está sendo processada...", ephemeral=True)
        
        try:
            with open(self.frimg(interaction.user.id, "imagem"), 'rb') as img:
                result = remove(img.read())
                buffer = io.BytesIO(result)
                result_final = Image.open(buffer).convert("RGBA")
                buffer.seek(0)
                
                img_dc_file = discord.File(buffer, filename="bg_removed.png")
        except Exception as e:
            return await interaction.followup.send("❌ Ocorreu um erro ao editar imagem!")
        
        embed = discord.Embed(
            title="Imagem com o fundo removido.",
            description="Perfeito! Não acha?",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"{interaction.user.name}").set_image(url="attachment://bg_removed.png")
        
        await interaction.followup.send(file=img_dc_file, embed=embed)
        
    @discord.ui.button(label="Corrigir Cores.", style=discord.ButtonStyle.grey, custom_id="ccm_btn", row=3)
    async def color_correction_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        try:
            with Image.open(self.frimg(interaction.user.id, "imagem")) as img:
                
                img = ImageEnhance.Brightness(img).enhance(1.1)
                img = ImageEnhance.Contrast(img).enhance(1.2)
                img = ImageEnhance.Color(img).enhance(1.1)
                
                img.save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
        except Exception as e:
            return await interaction.response.send_message(f"❌ Ocorreu um erro ao editar imagem!\n {e}")
            
        await interaction.response.send_message("✅ Imagem editada com sucesso!")
        
    @discord.ui.button(label="Melhorar Qualidade.", style=discord.ButtonStyle.grey, custom_id="up_quality", row=3)
    async def update_quality_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        try:
            with Image.open(self.frimg(interaction.user.id, "imagem")) as img:
                
                img.filter(ImageFilter.SHARPEN)
                img = ImageEnhance.Brightness(img).enhance(1.2)
                img = ImageEnhance.Contrast(img).enhance(1.1)
                img = ImageEnhance.Color(img).enhance(1.15)
                
                img.save(f"image_editor_path/{interaction.user.id}.png", format="PNG")
        except Exception as e:
            return await interaction.response.send_message(f"❌ Ocorreu um erro ao editar imagem!\n {e}")
        
        await interaction.response.send_message("✅ Imagem editada com sucesso!")
        
    @discord.ui.button(label="Ver Imagem.", style=discord.ButtonStyle.blurple, custom_id="viewer_image_final", row=1)
    async def ver_imagem_final(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        try:
            img_path = f"image_editor_path/{interaction.user.id}.png"
            img_final = discord.File(img_path, filename=f"{interaction.user.name}.png")
        except:
            return await interaction.response.send_message("❌ Imagem não foi encontrada, tem certeza que enviou alguma imagem?", ephemeral=True)
                
        embed = discord.Embed(
            title=f"Imagem editada do {interaction.user.display_name}",
            description="O que você achou?",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {interaction.user.name}", icon_url=interaction.user.avatar.url).set_image(url=f"attachment://{interaction.user.name}.png")
        
        await interaction.response.send_message(embed=embed, file=img_final, ephemeral=True)
        
    @discord.ui.button(label="Excluir Imagem.", style=discord.ButtonStyle.red, custom_id="delete_image", row=1)
    async def delete_image_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        if self.author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
    
        try:
            os.remove(f"image_editor_path/{interaction.user.id}.png")
        except:
            return await interaction.response.send_message("❌ Houve um erro ao exlcuir imagem, tem certeza que enviou alguma imagem?", ephemeral=True)
            
        await interaction.response.send_message("✅ Imagem excluída com sucesso!" , ephemeral=True)

def glitch_frame(img, max_offset=10):
    r, g, b, *rest = img.split()  

    r = ImageChops.offset(r, random.randint(-max_offset, max_offset), random.randint(-max_offset, max_offset))
    g = ImageChops.offset(g, random.randint(-max_offset, max_offset), random.randint(-max_offset, max_offset))
    b = ImageChops.offset(b, random.randint(-max_offset, max_offset), random.randint(-max_offset, max_offset))
    if rest:
        img_glitch = Image.merge("RGBA", (r, g, b, rest[0]))
    else:
        img_glitch = Image.merge("RGB", (r, g, b))
    return img_glitch

def ddlc_filter(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    width, height = img.size

    # 1️⃣ Converte para sépia
    sepia = Image.new("RGB", img.size)
    pixels = img.load()
    sepia_pixels = sepia.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            sepia_pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))

    # 2️⃣ Ajuste leve de brilho e contraste (pra suavizar)
    sepia = ImageEnhance.Brightness(sepia).enhance(1.05)
    sepia = ImageEnhance.Contrast(sepia).enhance(1.1)
    sepia = ImageEnhance.Color(sepia).enhance(1.2)

    # 3️⃣ Adiciona ruído suave (granulação)
    pixels = sepia.load()
    for _ in range(int(width * height * 0.01)):  # 1% dos pixels
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        noise = random.randint(-20, 20)
        r, g, b = pixels[x, y]
        pixels[x, y] = (
            max(0, min(255, r + noise)),
            max(0, min(255, g + noise)),
            max(0, min(255, b + noise))
        )

    # 4️⃣ Pequeno vinhete para o toque "DDLC menu"
    vignette = Image.new("L", (width, height))
    for y in range(height):
        for x in range(width):
            dx = abs(x - width // 2) / (width / 2)
            dy = abs(y - height // 2) / (height / 2)
            dist = (dx ** 2 + dy ** 2) ** 0.5
            vignette.putpixel((x, y), int(255 * (1 - dist * 0.8)))

    sepia.putalpha(vignette)
    final = Image.alpha_composite(Image.new("RGBA", sepia.size, (0, 0, 0, 0)), sepia)
    return final.convert("RGB")

class ImageCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
    @commands.command(name="editor")
    async def image_editor(ctx:commands.Context):
        
        embed = discord.Embed(
            title="🈹 Editor de Imagem do Keith.",
            description="🔮 Aqui você pode escolher quais edições fazer na sua imagem.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
        
        await ctx.reply(embed=embed, view=ButtonAndViewImageEditor(ctx.author.id))
        
    @commands.command(name="blur")
    async def blur_avatar(self, ctx:commands.Context, blur_effect:int = None, user:discord.User = None):
        
        if blur_effect is None:
            return await ctx.send("❗️ Digite o nível do efeito Blur, máximo de 10, miníno de 1")
        
        if blur_effect > 10:
            return await ctx.send("❗️ O efeito blur não deve ser maior que 10!")
        
        if blur_effect is None:
            return await ctx.send("❗️ Você deve usar o comando assim: <blur [numero do efeito blur(no máximo 10)] [user(opcional)]")
        
        if user is None:
            user = ctx.author
            
        avatar_bytes = await get_avatar(user.display_avatar.url)
        
        with Image.open(avatar_bytes) as avatar:
            blurred = avatar.filter(ImageFilter.GaussianBlur(blur_effect))
            
            buffer = io.BytesIO()
            blurred.save(buffer, format="PNG")
            buffer.seek(0)
            
        avatar_file = discord.File(buffer, filename="avatar.png")
        
        blurred_embed = discord.Embed(
            title="♨️ Avatar com efeito Blur",
            description="Aqui está o efeito blur no seu avatar!",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://avatar.png")
        
        await ctx.reply(file=avatar_file, embed=blurred_embed)
        
    @commands.command(name="wanted", aliases=["procurado", "cartaz-de-procurado"])
    async def wanted_poster(self, ctx:commands.Context, user:discord.User = None):
        
        if user is None:
            user = ctx.author
        
        bg = Image.open("assets/wanted_image2.jfif").convert("RGBA").resize((512, 800))
        avatar_bytes = await get_avatar(user.avatar.url)
        avatar_img = Image.open(avatar_bytes).convert("RGBA").resize((350, 350), Image.Resampling.LANCZOS)
        
        # Cria uma máscara (mesmo tamanho)
        size = 350
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)

        # Desenha um círculo branco (255)
        draw.ellipse((0, 0, size, size), fill=255)

        # Aplica a máscara no avatar
        rounded = Image.new("RGBA", (size, size))
        rounded.paste(avatar_img, (0, 0), mask=mask)
        
        bg.alpha_composite(rounded, (80, 250))
        
        buffer = io.BytesIO()
        bg.save(buffer, format="PNG")
        buffer.seek(0)
        
        file_bg = discord.File(buffer, filename="wanted.png")
        
        wanted_embed = discord.Embed(
            title=f"{user.display_name} está sendo procurado! ⚔️",
            description="Nós oferecemos uma recompensa\n de 100 mil doláres 💰 por ele!",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://wanted.png")
        
        await ctx.reply(embed=wanted_embed, file=file_bg)
        
    @commands.command(name="blackandwhite", aliases=["bw", "pretoebranco"])
    async def black_and_white(self, ctx:commands.Context, user:discord.User = None):
        
        user = user or ctx.author
        
        avatar_bytes = await get_avatar(user.avatar.url)
        
        with Image.open(avatar_bytes) as img:
            # Converte para escala de cinza
            bw = img.convert('L')
            
            buffer = io.BytesIO()
            bw.save(buffer, format='PNG')
            buffer.seek(0)
            
        file = discord.File(buffer, filename="bw.png")
        
        bw_embed = discord.Embed(
            title=f"{user.display_name}",
            description="Avatar preto e branco.",
            color=discord.Color.lighter_grey(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://bw.png")
        
        await ctx.send(file=file, embed=bw_embed)

    @commands.command(name="triggered")
    async def triggered_effect(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        # Baixa o avatar
        avatar_bytes = await get_avatar(member.display_avatar.url)

        with Image.open(avatar_bytes).convert("RGB") as base_img:
            # Redimensiona para HD quadrado (1080x1080)
            base_img = base_img.resize((1080, 1080), Image.Resampling.LANCZOS)

            frames = []
            for i in range(8):  # mais frames = efeito mais intenso
                # Overlay vermelho
                overlay = Image.new("RGB", base_img.size, (255, 0, 0))
                blended = Image.blend(base_img, overlay, 0.4)

                # Tremor aleatório
                offset = (random.randint(-30, 30), random.randint(-30, 30))
                frame = Image.new("RGB", base_img.size, (0, 0, 0))
                frame.paste(blended, offset)

                # Texto "TRIGGERED"
                draw = ImageDraw.Draw(frame)
                try:
                    font = ImageFont.truetype("arial.ttf", 150)
                except:
                    font = ImageFont.load_default()

                text = "TRIGGERED"

                # Medição do texto compatível com Pillow >=10
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                except AttributeError:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                text_x = (frame.width - text_width) / 2
                text_y = frame.height - text_height - 30

                # Fundo vermelho para o texto
                draw.rectangle(
                    [(0, text_y - 10), (frame.width, frame.height)],
                    fill=(255, 0, 0)
                )
                # Texto branco com sombra
                draw.text((text_x + 5, text_y + 5), text, font=font, fill=(0, 0, 0))
                draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

                frames.append(frame)

            # Salva GIF em memória
            buffer = io.BytesIO()
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=60,
                loop=0
            )
            buffer.seek(0)

        file = discord.File(buffer, filename="triggered.gif")

        embed = discord.Embed(
            title=f"{member.display_name}",
            description="🚨 Efeito TRIGGERED!",
            color=discord.Color.red()
        )
        embed.set_image(url="attachment://triggered.gif")
        embed.set_footer(
            text=f"Requisitado por {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(file=file, embed=embed)
        
    @commands.command(name="lgbtqipna+")
    async def gay_flag(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        
        avatar_bytes = await get_avatar(member.avatar.url)
        
        with Image.open(avatar_bytes) as img:
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            colors = [
                (255, 0, 0, 100),    # Vermelho
                (255, 165, 0, 100),  # Laranja
                (255, 255, 0, 100),  # Amarelo
                (0, 255, 0, 100),    # Verde
                (0, 0, 255, 100),    # Azul
                (75, 0, 130, 100)    # Roxo
            ]
            
            stripe_height = img.height // len(colors)
            for i, color in enumerate(colors):
                y0 = i * stripe_height
                y1 = (i + 1) * stripe_height
                draw.rectangle([0, y0, img.width, y1], fill=color)
            
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            result = Image.alpha_composite(img, overlay)
            
            buffer = io.BytesIO()
            result.save(buffer, format='PNG')
            buffer.seek(0)

        file = discord.File(buffer, filename="gay_flag.png")
            
        _embed = discord.Embed(
            title=f"{member.display_name}",
            description="Avatar preto e branco.",
            color=discord.Color.lighter_grey(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://gay_flag.png")
            
        await ctx.send(file=file, embed=_embed)
        
    @commands.command(name="mirror", aliases=["espelhar", "espelho"])
    async def mirror_avatar(self, ctx:commands.Context, user:discord.User = None):
        
        if user is None:
            user = ctx.author
            
        avatar_bytes = await get_avatar(user.avatar.url)
        with Image.open(avatar_bytes) as img:
            mirrored = ImageOps.mirror(img)
            
            buffer = io.BytesIO()
            mirrored.save(buffer, format="PNG")
            buffer.seek(0)
            
        file_img = discord.File(buffer, filename="mirror.png")
            
        _embed = discord.Embed(
            title=f"{user.display_name}",
            description="Avatar espelhado",
            color=discord.Color.lighter_grey(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://mirror.png")
        
        await ctx.reply(file=file_img, embed=_embed)
        
    @commands.command(name="invert", aliases=["invertercores", "ic"])
    async def ic_command(self, ctx:commands.Context, user:discord.User = None):

        if user is None:
            user = ctx.author
            
        avatar_bytes = await get_avatar(user.avatar.url)
        with Image.open(avatar_bytes).convert("RGB") as img:
            img = ImageOps.invert(img)
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
        img_file = discord.File(buffer, filename="invertido.png")
        
        _embed = discord.Embed(
            title=f"{user.display_name}",
            description="Avatar com cores invertida.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://invertido.png")
        
        await ctx.reply(file=img_file, embed=_embed)
        
    @commands.command(name="collage")
    async def avatar_collage(self, ctx, *members: discord.Member):
        if not members:
            members = [ctx.author]
        
        members = members[:9]
        
        size = 300
        cols = 3
        rows = (len(members) + cols - 1) // cols
        
        collage = Image.new('RGB', (cols * size, rows * size), color='white')
        
        for i, member in enumerate(members):
            avatar_bytes = await get_avatar(member.avatar.url)
            
            with Image.open(avatar_bytes) as avatar:
                avatar = avatar.resize((size, size))
                
                x = (i % cols) * size
                y = (i // cols) * size
                
                collage.paste(avatar, (x, y))
        
        buffer = io.BytesIO()
        collage.save(buffer, format='PNG')
        buffer.seek(0)
        
        file = discord.File(buffer, filename="collage.png")
        await ctx.send(file=file)
        
    @commands.command(name="futuroservidor")
    async def avatar_collage(self, ctx, *members: discord.Member):
        
        titles = [
            "Futuro Moderador",
            "Futuro Banido",
            "Futuro Dono",
            "Futuro Warnado",
            "Futuro Mutado",
            "Futuro Staff"
        ]
        
        members = list(members)[:6] if members else [ctx.author]
        
        guild_members = [m for m in ctx.guild.members if not m.bot]
        
        available_members = [m for m in guild_members if m not in members]
        
        while len(members) < 6 and available_members:
            m = random.choice(available_members)
            members.append(m)
            available_members.remove(m)
        
        size = 300
        cols = 3
        rows = 2
        padding = 50  
        collage = Image.new("RGB", (cols * size, rows * (size + padding)), color="white")
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        for i, member in enumerate(members):
            avatar_bytes = await get_avatar(member.display_avatar.url)
            with Image.open(avatar_bytes) as avatar:
                avatar = avatar.resize((size, size))
                mask = Image.new("L", (size, size), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, size, size), fill=255)
                avatar = ImageOps.fit(avatar, (size, size))
                avatar.putalpha(mask)
                
                x = (i % cols) * size
                y = (i // cols) * (size + padding)
                
                collage.paste(avatar, (x, y), avatar)
                
                draw = ImageDraw.Draw(collage)
                text = titles[i]
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                except AttributeError:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                text_x = x + (size - text_width) / 2
                text_y = y + size + 5
                draw.text((text_x, text_y), text, font=font, fill="black")
        
        buffer = io.BytesIO()
        collage.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(buffer, filename="collage.png")
        await ctx.send(file=file)
        
    @commands.command(name="deepfry")
    async def deep_fry(self, ctx, member: discord.Member = None):
        """Aplica efeito 'deep fry' no avatar (meme)"""
        member = member or ctx.author
        
        avatar_bytes = await get_avatar(member.avatar.url)
        
        with Image.open(avatar_bytes).convert("RGB") as img:
            img = ImageEnhance.Color(img).enhance(3.0)
            
            img = ImageEnhance.Contrast(img).enhance(2.0)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=10)  
            buffer.seek(0)
            
        file = discord.File(buffer, filename="deepfried.jpg")
        
        _embed = discord.Embed(
            title=f"{member.display_name}",
            description="Avatar com efeito Deepfry.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://deepfried.jpg")
        
        await ctx.send(file=file)

    @commands.command(name="glitch")
    async def glitch(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        avatar_bytes = await get_avatar(member.display_avatar.url)

        with Image.open(avatar_bytes) as img:
            img = img.convert("RGBA")
            frames = []
            for _ in range(8): 
                frame = glitch_frame(img, max_offset=15)
                frames.append(frame)

            buffer = io.BytesIO()
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=80,
                loop=0,
                disposal=2,
                optimize=False
            )
            buffer.seek(0)

        img_glitch = discord.File(buffer, "glitch.gif")

        _embed = discord.Embed(
            title=f"{member.display_name}",
            description="Avatar com efeito RGB Glitch.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://glitch.gif")

        await ctx.send(file=img_glitch)

    @commands.command(name="estatica", aliases=["static", "estaticatv"])
    async def tv_static_gif(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        avatar_bytes = await get_avatar(member.display_avatar.url)
        with Image.open(avatar_bytes).convert("RGB") as img:
            width, height = img.size
            frames = []

            for i in range(10):
                noise = Image.effect_noise((width, height), random.randint(50, 120))
                noise = noise.convert("RGB")

                frame = Image.blend(img, noise, alpha=0.5)

                frames.append(frame)

            buffer = io.BytesIO()
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0
            )
            buffer.seek(0)

        file = discord.File(buffer, filename="tv_static.gif")

        _embed = discord.Embed(
            title=f"{member.display_name}",
            description="Avatar com efeito de estática.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url).set_image(url="attachment://tv_static.gif")
        
        await ctx.send(file=file)

    @commands.command(name="pixelart")
    async def M8_bit_cga(self, ctx:commands.Context, quantity_pixels:int = None, user:discord.User = None):
        
        if user is None:
            user = ctx.author
            
        if quantity_pixels is None:
            return await ctx.send("❗️ Escolha uma quantidade de pixel para a pixel art, minímo de 32 e máximo de 128")

        if quantity_pixels > 128:
            return await ctx.send("❗️ Não ultrapasse os 128 pixels!")

        if quantity_pixels < 32:
            return await ctx.send("❗️ Não coloque menos de 32 pixels!")
            
        avatar_bytes = await get_avatar(user.avatar.url)
        sz = quantity_pixels
        with Image.open(avatar_bytes) as img:
            small = img.resize((sz, sz), Image.Resampling.NEAREST)
            
            cga_palette = [
                (0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
                (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
                (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
                (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)
            ]

            pal_img = Image.new("P", (1, 1))
            palette_flat = sum(cga_palette, ())  # transforma em uma tupla plana
            palette_flat += (0, 0, 0) * (256 - len(cga_palette))  # completa 256 cores
            pal_img.putpalette(palette_flat)
            
            final_img = small.resize(img.size, Image.Resampling.NEAREST)
            
            buffer = io.BytesIO()
            final_img.save(buffer, format="PNG")
            buffer.seek(0)
            
            file_buffer = discord.File(buffer, filename="8bit_CGA.png")
            
            await ctx.reply(file=file_buffer)
            
    @commands.command(name="vhs")
    async def vhs_avatar(self, ctx:commands.Context, member: discord.Member = None):
        member = member or ctx.author
        
        msg = await ctx.send("Carregando imagem, espere...")
        
        avatar_bytes = await get_avatar(member.display_avatar.url)
        
        with Image.open(avatar_bytes).convert("RGB") as img:
            sz = 512
            img = img.resize((sz, sz))  # tamanho fixo para o GIF
            frames = []
            
            # Cria 10 frames com glitch
            for _ in range(10):
                frame = add_vhs_glitch(img)
                frames.append(frame)
            
            # Salva GIF
            buffer = io.BytesIO()
            frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=80, loop=0)
            buffer.seek(0)
        
        file = discord.File(buffer, filename="vhs_avatar.gif")
        await msg.delete()
        await ctx.send(file=file)
        
    @commands.command(name="customglitch")
    async def glitch_command(self, ctx:commands.Context, tipo: str = None, member: discord.Member = None):
        
        if tipo is None:
            return await ctx.reply("Digite que tipo de glitch você quer.\n<customglitch [soft ou hard]")
        
        """Aplica um efeito glitch animado (soft ou hard) no avatar"""
        member = member or ctx.author
        tipo = tipo.lower()

        avatar_bytes = await get_avatar(member.display_avatar.url)
        with Image.open(avatar_bytes).convert("RGB") as img:
            img = img.resize((256, 256))  # reduz pra agilizar o envio
            frames = []

            # Gera 10 frames animados
            for _ in range(10):
                if tipo == "hard":
                    frame = hard_glitch(img)
                else:
                    frame = soft_glitch(img)
                frames.append(frame)

            # Salva como GIF
            buffer = io.BytesIO()
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=80,  # velocidade entre frames (ms)
                loop=0
            )
            buffer.seek(0)

        file = discord.File(buffer, filename="glitch.gif")
        embed = discord.Embed(
            title=f"🎛️ {tipo.capitalize()} Glitch",
            description=f"Efeito aplicado em {member.display_name}",
            color=discord.Color.red()
        )
        embed.set_image(url="attachment://glitch.gif")

        await ctx.send(file=file, embed=embed)

    @commands.command(name="retro", aliases=["retroavatar", "rva"])
    async def ddlc_command(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        avatar_bytes = await get_avatar(member.display_avatar.url)
        with Image.open(avatar_bytes) as img:
            img = img.resize((512, 512))
            filtered = ddlc_filter(img)

            buffer = io.BytesIO()
            filtered.save(buffer, format="PNG")
            buffer.seek(0)

        file = discord.File(buffer, filename="ddlc.png")
        embed = discord.Embed(
            title="Efeito Retrô.",
            description=f"Avatar de {member.display_name}",
            color=discord.Color.pink()
        )
        embed.set_image(url="attachment://ddlc.png")

        await ctx.send(file=file, embed=embed)

    @commands.command(name="glowneon")
    async def gn(self, ctx:commands.Context, user:discord.User = None):
        
        if user is None:
            user = ctx.author
        
        border_size = 8
        border_color = ImageColor.getrgb('#5600ff')
        avatar_bytes = await get_avatar(user.avatar.url)
        with Image.open(avatar_bytes).convert("RGBA") as img:
            
            mask = Image.new('L', img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, *img.size), fill=255)
            
            border_mask = ImageOps.expand(mask, border_size, fill=255)
            border = Image.new('RGBA', border_mask.size, border_color + (255,))
            
            border.putalpha(border_mask)
            
            base = Image.new("RGBA", border.size, (0, 0, 0, 0))
            offset = (border_size, border_size)
            base.paste(border, (0, 0), border)
            base.paste(img, offset, mask)
            
            buffer = io.BytesIO()
            base.save(buffer, format="PNG")
            buffer.seek(0)
            
            img_file = discord.File(buffer, filename="border_avatar.png")
            await ctx.reply(file=img_file)

    @commands.command(name="borderavatar")
    async def gn(self, ctx: commands.Context, user: discord.User = None):
        import aiohttp, io
        from PIL import Image, ImageDraw, ImageColor, ImageFilter

        if user is None:
            user = ctx.author

        border_size = 12  # tamanho da borda
        border_color = ImageColor.getrgb('#5600ff')

        # --- Baixar avatar ---
        async with aiohttp.ClientSession() as session:
            async with session.get(user.display_avatar.url) as resp:
                avatar_bytes = await resp.read()

        with Image.open(io.BytesIO(avatar_bytes)).convert("RGBA") as img:
            size = img.size[0] + border_size * 2
            base = Image.new("RGBA", (size, size), (0, 0, 0, 0))

            # --- Máscara circular para avatar ---
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)

            # --- Criar círculo maior pra borda ---
            border_mask = Image.new("L", (size, size), 0)
            draw_border = ImageDraw.Draw(border_mask)
            draw_border.ellipse(
                (0, 0, size, size),
                fill=255
            )

            # --- Círculo menor pra “recortar” o meio ---
            draw_border.ellipse(
                (border_size, border_size, size - border_size, size - border_size),
                fill=0
            )

            # --- Criar borda com cor desejada ---
            border_img = Image.new("RGBA", (size, size), border_color + (255,))
            border_img.putalpha(border_mask)

            # --- (Opcional) aplicar um blur leve pra efeito neon suave ---
            glow = border_img.filter(ImageFilter.GaussianBlur(6))

            # --- Compor imagem final ---
            base = Image.alpha_composite(base, glow)
            base.paste(img, (border_size, border_size), mask)

            # --- Enviar ---
            buffer = io.BytesIO()
            base.save(buffer, format="PNG")
            buffer.seek(0)

            await ctx.reply(file=discord.File(buffer, filename="glowneon.png"))

    @commands.command(name="editorsettings", aliases=["configseditor"])
    async def editor_settings(self, ctx:commands.Context):
        
        
        embed = discord.Embed(
        title="Configurações do Editor de Imagem.",
        description="Aqui você pode configurar algumas coisas do seu editor de imagem.",
        color=discord.Color.purple(),
        timestamp=discord.utils.utcnow()
        ).set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url).set_thumbnail(url=ctx.guild.icon.url)
        
        await ctx.reply(embed=embed, view=ButtonsSettingsEditor(ctx.author.id))

        class ButtonsSettingsEditor(discord.ui.View):
            def __init__(self, ctx_author_id):
                super().__init__(timeout=120)
                self.ctx_author_id = ctx_author_id
                self.add_item(self.ButtonForBorderEditorMode())
                
            class ButtonForBorderEditorMode(discord.ui.Button):
                def __init__(self):
                    super().__init__(label="Modo do seu editor de Borda.", style=discord.ButtonStyle.grey, custom_id="settings_btn")
        
                async def callback(self, interaction:discord.Interaction):
                    
                    if ctx.author.id !=  interaction.user.id:
                        return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
                    
                    class ModalForMode(discord.ui.Modal):
                        def __init__(self):
                            super().__init__(title="Imagem Quadrada ou Circular?")
                    
                            self.input1 = discord.ui.TextInput(label="Modo: Quadrada/Circular", placeholder="Ex: Quadrada/Circular", max_length=15, required=True)
                            self.add_item(self.input1)
                            
                        async def on_submit(self, interaction:discord.Interaction):
                            
                            async with AsyncSessionReze() as session:
                                result = await session.execute(select(ModeOfTheBorderEditor).filter_by(user_id=interaction.user.id))
                                userdb = result.scalars().first()
                                if not userdb:
                                    userdb = ModeOfTheBorderEditor(user_id=ctx.author.id, mode=self.input1.value)
                                    session.add(userdb)
                                userdb.mode = self.input1.value
                                await session.commit()
                            
                            await interaction.response.send_message("✅ Modo alterado com sucesso!", ephemeral=True)
                    
                    await interaction.response.send_modal(ModalForMode())
                    
async def setup(bot):
    await bot.add_cog(ImageCog(bot))