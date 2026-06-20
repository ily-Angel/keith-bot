# functionspillow.py - Versão corrigida e otimizada
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from dbdata import Base, UserMDBs, CorridaUsersRandons, VipsUserMdbs, DailyCooldown, RoletaDiariaCooldown, AsyncSessionLocal, init_db, XpGlobal, UserXP, ChannelLogsConfiguration
import sqlite3
from datetime import datetime 
import psutil
import io
import random
from sqlalchemy import select
import logging
import pytz
from datetime import timedelta
from typing import Optional
import platform
from discord.ui import Modal, View, Button
from discord.ext.commands import when_mentioned_or
from PIL import Image, ImageChops, ImageDraw, ImageColor, ImageFilter, ImageFont
import re
import requests
import unicodedata
from io import BytesIO
import disnake
import cairo
import aiohttp
from sqlalchemy import DateTime, String, Integer, create_engine, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from discord.ext import tasks
from typing import List
import math
from dbdata_server import AsyncSessionServerConfigs, DataForExtrasForGoodbyeMessage, DataForExtrasForWelcomeMessage, DataForGoodbyeMessage, BancoDeDadosParaMensagemDeBemVindoPersonalizada
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Date, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from PIL import Image
from dbdata import PremiumDataSuper, AsyncSessionLocal

import functions as funcs

# =========================
# CONSTANTES
# =========================

FONTES_DISPONIVEIS = {
    "aquire": "fonts/Aquire-BW0ox.otf",
    "orbitron": "fonts/Orbitron-VariableFont_wght.ttf",
    "cyberpunk": "fonts/Cyberpunk.ttf",
    "blad": "fonts/BLADRMF_.TTF",
    "playfair": "fonts/PlayfairDisplay-VariableFont_wght.ttf",
    "quantico": "fonts/Quantico-Italic.ttf",
    "horrendo": "fonts/horrendo.ttf",
    "arial": "fonts/arial.ttf",
    "cinzel": "fonts/CinzelDecorative-Regular.ttf",
    "pf uniform": "fonts/pf_uniform.ttf",
    "monad": "fonts/Monad.otf",
    "morena": "fonts/Morena.otf",
    "astra": "fonts/Astra-6RGXq.otf",
    "alexana": "fonts/Alexana.ttf",
    "nordic": "fonts/Nordic.ttf",
    "transformers": "fonts/Transformers.ttf",
    "optimus princeps": "fonts/Optimus_Princeps.ttf",
    "azonix": "fonts/Azonix.otf",
    "andromeda": "fonts/Andromeda-Bold.otf",
    "meroona": "fonts/Meroona.otf",
    "zector": "fonts/Zector.ttf",
    "nebula": "fonts/Nebula-Regular.otf",
    "aquatico": "fonts/Aquatico-Regular.otf",
    "gyre termes": "fonts/tex-gyre-termes.italic.otf",
}

FONTE_PADRAO = "fonts/arial.ttf"

# =========================
# FUNÇÕES DE UTILIDADE
# =========================

def caminho_da_fonte(nome_fonte: str) -> str:
    if not nome_fonte:
        return FONTE_PADRAO
    return FONTES_DISPONIVEIS.get(nome_fonte.lower(), FONTE_PADRAO)

def limpar_unicode(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto)
    return ''.join(c for c in texto if c.isprintable())

def is_valid_hex(cor: str) -> bool:
    import re
    return bool(re.match(r"^#[0-9A-Fa-f]{6}$", cor))

# =========================
# FUNÇÃO DE GRADIENTE (UNIFICADA)
# =========================

def apply_gradient_text(draw, position, text, font, colors, background_image, default_color="#FFFFFF"):
    if not colors or len(colors) < 1:
        draw.text(position, text, font=font, fill=ImageColor.getrgb(default_color))
        return
    
    x, y = position
    
    temp_img = Image.new('RGBA', background_image.size, (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    temp_draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    bbox = temp_img.getbbox()
    if not bbox:
        draw.text((x, y), text, font=font, fill=ImageColor.getrgb(default_color))
        return
    
    text_left, text_top, text_right, text_bottom = bbox
    text_width = text_right - text_left
    text_height = text_bottom - text_top
    
    if text_width <= 0 or text_height <= 0:
        draw.text((x, y), text, font=font, fill=ImageColor.getrgb(default_color))
        return
    
    gradient = Image.new('RGB', (text_width, text_height))
    gradient_draw = ImageDraw.Draw(gradient)
    
    num_colors = len(colors)
    
    if num_colors == 1:
        color = ImageColor.getrgb(colors[0])
        gradient_draw.rectangle([0, 0, text_width, text_height], fill=color)
    
    elif num_colors == 2:
        color1 = ImageColor.getrgb(colors[0])
        color2 = ImageColor.getrgb(colors[1])
        for i in range(text_width):
            ratio = i / text_width
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            gradient_draw.line([(i, 0), (i, text_height)], fill=(r, g, b))
    
    else:
        segments = num_colors - 1
        segment_width = text_width // segments
        
        for seg in range(segments):
            color_start = ImageColor.getrgb(colors[seg])
            color_end = ImageColor.getrgb(colors[seg + 1])
            
            start_x = seg * segment_width
            end_x = (seg + 1) * segment_width if seg < segments - 1 else text_width
            
            for i in range(start_x, end_x):
                ratio = (i - start_x) / (end_x - start_x)
                r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
                gradient_draw.line([(i, 0), (i, text_height)], fill=(r, g, b))
    
    gradient_rgba = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
    text_region = temp_img.crop(bbox)
    
    for i in range(text_width):
        for j in range(text_height):
            text_pixel = text_region.getpixel((i, j))
            if text_pixel[3] > 0:
                grad_color = gradient.getpixel((i, j))
                gradient_rgba.putpixel((i, j), grad_color + (text_pixel[3],))
    
    background_image.paste(gradient_rgba, (text_left, text_top), gradient_rgba)

# =========================
# FUNÇÕES DE OBTENÇÃO DE DADOS (USANDO functions.py)
# =========================

async def obter_fonte_e_tamanhos(user_id: int):
    fonte_nome = await funcs.get_fonte(user_id)
    caminho = caminho_da_fonte(fonte_nome)
    
    font_sizes = await funcs.get_font_sizes(user_id)
    
    return caminho, font_sizes.font_nome_px, font_sizes.font_bio_px, font_sizes.font_xp_px

async def obter_configs_perfil(user_id: int):
    cfg = await funcs.load_config(user_id)
    
    perfil_size = await funcs.get_perfil_size(user_id)
    
    perfil_border = await funcs.get_perfil_border(user_id)
    
    gradient_colors = await funcs.get_gradient_colors(user_id)
    
    perfil_model = await funcs.get_perfil_model(user_id)
    
    return {
        "cfg": cfg,
        "perfil_size": perfil_size,
        "perfil_border": perfil_border,
        "gradient_colors": gradient_colors,
        "perfil_model": perfil_model
    }

async def verificar_premium(user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PremiumDataSuper).filter_by(user_id=user_id))
        return result.scalars().first() is not None

# =========================
# LAYOUT 1 - PERFIL (OTIMIZADO)
# =========================

async def desenhar_layout_perfil(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro=None, fonte=None, userid=None):
    user_id = userid or user.id
    
    configs = await obter_configs_perfil(user_id)
    perfil_size = configs["perfil_size"]
    perfil_border = configs["perfil_border"]
    gradient_colors = configs["gradient_colors"]
    is_premium = await verificar_premium(user_id)
    
    altura = perfil_size.altura_p or 300
    curvatura = perfil_size.altura_da_faixa or 1
    translucidez_da_faixa = perfil_size.translucides_da_faixa or 150
    
    caminho_fonte, pxnome, pxbio, pxxp = await obter_fonte_e_tamanhos(user_id)
    
    nivel, restante_xp, total_xp, xp_universal = xp_info
    mostrar_xp = cfg.get("mostrar_xp_bar", False)
    cor_barra = cfg.get("xp_bar_color", "#64B4FF")
    
    escala = 0.84
    at = 300
    at_f = altura / 2
    at_f2 = altura * 0.56
    at_f3 = altura * 0.20 * curvatura
    
    largura_total, altura_total = int(800 * escala), int(altura * escala)
    avatar_tamanho = int(128 * escala)
    faixa_largura = int(900 * 0.95 * escala)
    faixa_altura = int(at_f * escala)
    raio = int(at_f3 * escala)
    faixa_y = int(at_f2 * escala - 10)
    
    bg = await carregar_fundo_perfil(user, largura_total, altura_total, cfg)
    
    avatar_final = preparar_avatar(avatar_img, avatar_tamanho, cfg.get("layout_avatar", "perfil"))
    
    faixa_transparente = preparar_faixa(
        faixa_largura, faixa_altura, 
        cfg.get("perfil_faixa_color", "#1E1E1E"), 
        translucidez_da_faixa, raio
    )
    
    bg.paste(faixa_transparente, (0, faixa_y), faixa_transparente)
    
    draw = ImageDraw.Draw(bg)
    
    try:
        font_nome = ImageFont.truetype(caminho_fonte, int(pxnome * escala))
        font_bio = ImageFont.truetype(caminho_fonte, int(pxbio * escala))
        font_xp = ImageFont.truetype(caminho_fonte, int(pxxp * escala))
    except:
        font_nome = ImageFont.truetype(FONTE_PADRAO, int(pxnome * escala))
        font_bio = ImageFont.truetype(FONTE_PADRAO, int(pxbio * escala))
        font_xp = ImageFont.truetype(FONTE_PADRAO, int(pxxp * escala))
    
    nome_position = (int(175 * escala), faixa_y + int(22 * escala))
    if is_premium and gradient_colors:
        apply_gradient_text(
            draw, nome_position, nome_visivel, font_nome, 
            gradient_colors, bg, cfg.get("color", "#FFFFFF")
        )
    else:
        draw.text(nome_position, nome_visivel, font=font_nome, fill=ImageColor.getrgb(cfg.get("color", "#FFFFFF")))
    
    draw.text((int(180 * escala), faixa_y + int(72 * escala)), bio, font=font_bio, fill="lightgray")
    
    if cfg.get("mostrar_casamento") and not mostrar_xp and parceiro:
        desenhar_casamento(bg, draw, user, parceiro, faixa_y, escala, font_bio)
    
    if mostrar_xp:
        desenhar_barra_xp(bg, draw, nivel, restante_xp, cor_barra, faixa_y, escala, font_xp, caminho_fonte)
    
    bg.paste(avatar_final, (int(30 * escala), int(faixa_y + 10 * escala)), avatar_final)
    
    if cfg.get("mostrar_badges", True) and badge_imgs:
        desenhar_badges(bg, badge_imgs, faixa_y, escala)
    
    return salvar_imagem(bg)

# =========================
# LAYOUT 2 - XP (OTIMIZADO)
# =========================

async def desenhar_layout_xp(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro=None, fonte=None):
    user_id = user.id
    
    configs = await obter_configs_perfil(user_id)
    perfil_size = configs["perfil_size"]
    gradient_colors = configs["gradient_colors"]
    is_premium = await verificar_premium(user_id)
    
    altura = perfil_size.altura_p or 240
    transparencia = perfil_size.translucides_da_faixa or 180
    
    nivel, restante_xp, total_xp, xp_universal = xp_info
    
    caminho_fonte, pxnome, pxbio, pxxp = await obter_fonte_e_tamanhos(user_id)
    
    largura, altura = 600, altura
    padding_x = 30
    avatar_tamanho = 96
    barra_largura = 300
    barra_altura = 30
    espacamento_vertical = math.floor(altura * 0.033)
    faixa_radius = 30
    
    cor_faixa = cfg.get("perfil_faixa_color", "#1E1E1E")
    cor_barra = cfg.get("xp_bar_color", "#64B4FF")
    cor_texto = cfg.get("xp_text_color", "#FFFFFF")
    cor_nome = cfg.get("color", "#2F3136")
    
    bg = await carregar_fundo_xp(user, largura, altura)
    
    faixa_x, faixa_y = 20, 20
    faixa_largura, faixa_altura = largura - 40, altura - 40
    
    faixa_canvas = Image.new("RGBA", (faixa_largura, faixa_altura), (0, 0, 0, 0))
    try:
        faixa_rgb = ImageColor.getrgb(cor_faixa)
    except:
        faixa_rgb = (60, 60, 60)
    
    faixa_cinza = Image.new("RGBA", (faixa_largura, faixa_altura), (*faixa_rgb, transparencia))
    faixa_mask = Image.new("L", (faixa_largura, faixa_altura), 0)
    ImageDraw.Draw(faixa_mask).rounded_rectangle((0, 0, faixa_largura, faixa_altura), radius=faixa_radius, fill=255)
    faixa_canvas.paste(faixa_cinza, (0, 0), faixa_mask)
    bg.alpha_composite(faixa_canvas, dest=(faixa_x, faixa_y))
    
    avatar = preparar_avatar_xp(avatar_img, avatar_tamanho, cfg.get("layout_avatar", "perfil"))
    avatar_y = faixa_y + (faixa_altura - avatar_tamanho) // 2 - 17
    bg.paste(avatar, (padding_x, avatar_y), avatar)
    
    draw = ImageDraw.Draw(bg)
    
    try:
        fonte_nome = ImageFont.truetype(caminho_fonte, pxnome)
        fonte_bio = ImageFont.truetype(caminho_fonte, pxbio)
        fonte_xp = ImageFont.truetype(caminho_fonte, pxxp)
    except:
        fonte_nome = ImageFont.truetype(FONTE_PADRAO, pxnome)
        fonte_bio = ImageFont.truetype(FONTE_PADRAO, pxbio)
        fonte_xp = ImageFont.truetype(FONTE_PADRAO, pxxp)
    
    info_x = padding_x + avatar_tamanho + 20
    centro_y = faixa_y + faixa_altura // 2
    
    nome_position = (info_x, centro_y - barra_altura - espacamento_vertical - 28)
    if is_premium and gradient_colors:
        apply_gradient_text(
            draw, nome_position, nome_visivel, fonte_nome,
            gradient_colors, bg, cor_nome
        )
    else:
        draw.text(nome_position, nome_visivel, font=fonte_nome, fill=cor_nome)
    
    draw.text((info_x, centro_y - barra_altura - 8), bio, font=fonte_bio, fill="lightgray")
    
    if cfg.get("mostrar_xp_bar", True):
        desenhar_barra_xp_layout2(
            bg, draw, nivel, restante_xp, cor_barra, cor_texto,
            info_x, centro_y, barra_largura, barra_altura, fonte_xp
        )
    
    if cfg.get("mostrar_casamento") and parceiro:
        barra_x = info_x
        barra_y = centro_y + 2
        desenhar_casamento_xp(bg, draw, user, parceiro, barra_x, barra_y, barra_altura, fonte_xp)
    
    if cfg.get("mostrar_badges", True) and badge_imgs:
        desenhar_badges_xp(bg, badge_imgs, largura)
    
    return salvar_imagem(bg)

# =========================
# LAYOUTS GIF (OTIMIZADOS)
# =========================

async def desenhar_layout_perfil_gif(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro=None, fonte=None, userid=None):
    user_id = userid or user.id
    
    configs = await obter_configs_perfil(user_id)
    perfil_size = configs["perfil_size"]
    gradient_colors = configs["gradient_colors"]
    is_premium = await verificar_premium(user_id)
    
    altura = perfil_size.altura_p or 300
    curvatura = perfil_size.altura_da_faixa or 1
    translucidez_da_faixa = perfil_size.translucides_da_faixa or 150
    
    nivel, restante_xp, total_xp, xp_universal = xp_info
    mostrar_xp = cfg.get("mostrar_xp_bar", False)
    cor_barra = cfg.get("xp_bar_color", "#64B4FF")
    
    escala = 0.84
    at = 300
    at_f = altura / 2
    at_f2 = altura * 0.56
    at_f3 = altura * 0.20 * curvatura
    
    largura_total, altura_total = int(800 * escala), int(altura * escala)
    avatar_tamanho = int(128 * escala)
    faixa_largura = int(900 * 0.95 * escala)
    faixa_altura = int(at_f * escala)
    raio = int(at_f3 * escala)
    faixa_y = int(at_f2 * escala - 10)
    
    caminho_fonte, pxnome, pxbio, pxxp = await obter_fonte_e_tamanhos(user_id)
    
    bg_gif = await carregar_fundo_gif(user, largura_total, altura_total, cfg)
    
    avatar_final = preparar_avatar(avatar_img, avatar_tamanho, cfg.get("layout_avatar", "perfil"))
    faixa_transparente = preparar_faixa(
        faixa_largura, faixa_altura,
        cfg.get("perfil_faixa_color", "#1E1E1E"),
        translucidez_da_faixa, raio
    )
    
    try:
        font_nome = ImageFont.truetype(caminho_fonte, int(pxnome * escala))
        font_bio = ImageFont.truetype(caminho_fonte, int(pxbio * escala))
        font_xp = ImageFont.truetype(caminho_fonte, int(pxxp * escala))
    except:
        font_nome = ImageFont.truetype(FONTE_PADRAO, int(pxnome * escala))
        font_bio = ImageFont.truetype(FONTE_PADRAO, int(pxbio * escala))
        font_xp = ImageFont.truetype(FONTE_PADRAO, int(pxxp * escala))
    
    frames = []
    
    try:
        from PIL import ImageSequence
        
        for frame in ImageSequence.Iterator(bg_gif):
            bg_frame = frame.convert("RGBA").resize((largura_total, altura_total))
            
            bg_frame.paste(faixa_transparente, (0, faixa_y), faixa_transparente)
            
            draw = ImageDraw.Draw(bg_frame)
            
            nome_position = (int(175 * escala), faixa_y + int(22 * escala))
            if is_premium and gradient_colors:
                apply_gradient_text(
                    draw, nome_position, nome_visivel, font_nome,
                    gradient_colors, bg_frame, cfg.get("color", "#FFFFFF")
                )
            else:
                draw.text(nome_position, nome_visivel, font=font_nome, fill=ImageColor.getrgb(cfg.get("color", "#FFFFFF")))
            
            draw.text((int(180 * escala), faixa_y + int(72 * escala)), bio, font=font_bio, fill="lightgray")
            
            if cfg.get("mostrar_casamento") and not mostrar_xp and parceiro:
                desenhar_casamento(bg_frame, draw, user, parceiro, faixa_y, escala, font_bio)
            
            if mostrar_xp:
                desenhar_barra_xp(bg_frame, draw, nivel, restante_xp, cor_barra, faixa_y, escala, font_xp, caminho_fonte)
            
            bg_frame.paste(avatar_final, (int(30 * escala), int(faixa_y + 10 * escala)), avatar_final)
            
            if cfg.get("mostrar_badges", True) and badge_imgs:
                desenhar_badges(bg_frame, badge_imgs, faixa_y, escala)
            
            frames.append(bg_frame)
    
    except (AttributeError, TypeError):
        bg_frame = bg_gif.convert("RGBA").resize((largura_total, altura_total))
        bg_frame.paste(faixa_transparente, (0, faixa_y), faixa_transparente)
        frames = [bg_frame]
    
    return salvar_gif(frames, bg_gif)

async def desenhar_layout_xp_gif(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro=None, fonte=None):
    """
    Desenha layout de XP com suporte a GIF animado.
    """
    user_id = user.id
    
    configs = await obter_configs_perfil(user_id)
    perfil_size = configs["perfil_size"]
    gradient_colors = configs["gradient_colors"]
    is_premium = await verificar_premium(user_id)
    
    altura = perfil_size.altura_p or 240
    transparencia = perfil_size.translucides_da_faixa or 180
    
    nivel, restante_xp, total_xp, xp_universal = xp_info
    
    caminho_fonte, pxnome, pxbio, pxxp = await obter_fonte_e_tamanhos(user_id)
    
    largura, altura = 600, altura
    padding_x = 30
    avatar_tamanho = 96
    barra_largura = 300
    barra_altura = 30
    espacamento_vertical = math.floor(altura * 0.033)
    faixa_radius = 30
    
    cor_faixa = cfg.get("perfil_faixa_color", "#1E1E1E")
    cor_barra = cfg.get("xp_bar_color", "#64B4FF")
    cor_texto = cfg.get("xp_text_color", "#FFFFFF")
    cor_nome = cfg.get("color", "#2F3136")
    
    bg_gif = await carregar_fundo_gif(user, largura, altura, cfg)
    
    faixa_x, faixa_y = 20, 20
    faixa_largura, faixa_altura = largura - 40, altura - 40
    
    try:
        faixa_rgb = ImageColor.getrgb(cor_faixa)
    except:
        faixa_rgb = (60, 60, 60)
    
    faixa_canvas = Image.new("RGBA", (faixa_largura, faixa_altura), (0, 0, 0, 0))
    faixa_cinza = Image.new("RGBA", (faixa_largura, faixa_altura), (*faixa_rgb, transparencia))
    faixa_mask = Image.new("L", (faixa_largura, faixa_altura), 0)
    ImageDraw.Draw(faixa_mask).rounded_rectangle((0, 0, faixa_largura, faixa_altura), radius=faixa_radius, fill=255)
    faixa_canvas.paste(faixa_cinza, (0, 0), faixa_mask)
    
    avatar = preparar_avatar_xp(avatar_img, avatar_tamanho, cfg.get("layout_avatar", "perfil"))
    avatar_y = faixa_y + (faixa_altura - avatar_tamanho) // 2 - 17
    
    try:
        fonte_nome = ImageFont.truetype(caminho_fonte, pxnome)
        fonte_bio = ImageFont.truetype(caminho_fonte, pxbio)
        fonte_xp = ImageFont.truetype(caminho_fonte, pxxp)
    except:
        fonte_nome = ImageFont.truetype(FONTE_PADRAO, pxnome)
        fonte_bio = ImageFont.truetype(FONTE_PADRAO, pxbio)
        fonte_xp = ImageFont.truetype(FONTE_PADRAO, pxxp)
    
    frames = []
    
    try:
        from PIL import ImageSequence
        
        for frame in ImageSequence.Iterator(bg_gif):
            bg_frame = frame.convert("RGBA").resize((largura, altura))
            
            bg_frame.alpha_composite(faixa_canvas, dest=(faixa_x, faixa_y))
            
            bg_frame.paste(avatar, (padding_x, avatar_y), avatar)
            
            draw = ImageDraw.Draw(bg_frame)
            
            info_x = padding_x + avatar_tamanho + 20
            centro_y = faixa_y + faixa_altura // 2
            
            nome_position = (info_x, centro_y - barra_altura - espacamento_vertical - 28)
            if is_premium and gradient_colors:
                apply_gradient_text(
                    draw, nome_position, nome_visivel, fonte_nome,
                    gradient_colors, bg_frame, cor_nome
                )
            else:
                draw.text(nome_position, nome_visivel, font=fonte_nome, fill=cor_nome)
            
            draw.text((info_x, centro_y - barra_altura - 8), bio, font=fonte_bio, fill="lightgray")
            
            if cfg.get("mostrar_xp_bar", True):
                desenhar_barra_xp_layout2(
                    bg_frame, draw, nivel, restante_xp, cor_barra, cor_texto,
                    info_x, centro_y, barra_largura, barra_altura, fonte_xp
                )
            
            if cfg.get("mostrar_casamento") and parceiro:
                barra_x = info_x
                barra_y = centro_y + 2
                desenhar_casamento_xp(bg_frame, draw, user, parceiro, barra_x, barra_y, barra_altura, fonte_xp)
            
            if cfg.get("mostrar_badges", True) and badge_imgs:
                desenhar_badges_xp(bg_frame, badge_imgs, largura)
            
            frames.append(bg_frame)
    
    except (AttributeError, TypeError):
        bg_frame = bg_gif.convert("RGBA").resize((largura, altura))
        bg_frame.alpha_composite(faixa_canvas, dest=(faixa_x, faixa_y))
        frames = [bg_frame]
    
    return salvar_gif(frames, bg_gif)

# =========================
# FUNÇÕES AUXILIARES DE DESENHO
# =========================

def preparar_avatar(avatar_img, tamanho, layout):
    mask = Image.new("L", (tamanho, tamanho), 0)
    if layout == "xp":
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, tamanho, tamanho), radius=20, fill=255)
    else:
        ImageDraw.Draw(mask).ellipse((0, 0, tamanho, tamanho), fill=255)
    
    avatar_src = avatar_img.convert("RGBA").resize((tamanho, tamanho))
    avatar_final = Image.new("RGBA", (tamanho, tamanho))
    avatar_final.paste(avatar_src, (0, 0), mask)
    return avatar_final

def preparar_avatar_xp(avatar_img, tamanho, layout):
    mask = Image.new("L", (tamanho, tamanho), 0)
    if layout == "xp":
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, tamanho, tamanho), radius=20, fill=255)
    else:
        ImageDraw.Draw(mask).ellipse((0, 0, tamanho, tamanho), fill=255)
    
    avatar_src = avatar_img.convert("RGBA").resize((tamanho, tamanho))
    avatar_bg = Image.new("RGBA", (tamanho, tamanho), (30, 30, 30, 255))
    avatar_bg.paste(avatar_src, (0, 0), mask)
    return avatar_bg

def preparar_faixa(largura, altura, cor, translucidez, raio):
    try:
        faixa_rgb = ImageColor.getrgb(cor)
    except:
        faixa_rgb = (30, 30, 30)
    
    faixa = Image.new("RGBA", (largura, altura), (*faixa_rgb, translucidez))
    
    msk = Image.new("L", (largura, altura), 255)
    canto = Image.new("L", (raio * 2, raio * 2), 0)
    ImageDraw.Draw(canto).rounded_rectangle((0, 0, raio * 2, raio * 2), radius=raio, fill=255)
    msk.paste(canto.crop((raio, 0, raio * 2, raio)), (largura - raio, 0))
    faixa.putalpha(ImageChops.multiply(faixa.getchannel("A"), msk))
    
    return faixa

def desenhar_barra_xp(bg, draw, nivel, restante_xp, cor_barra, faixa_y, escala, font_xp, caminho_fonte):
    barra_x = int(285 * escala)
    barra_y = faixa_y + int(120 * escala)
    barra_largura = int(300 * escala)
    barra_altura = int(20 * escala)
    
    progresso = min(restante_xp / 1000, 1.0)
    barra_cheia = int(barra_largura * progresso)
    
    nivel_texto = f"Nivel XP: {nivel}"
    draw.text((barra_x - int(draw.textlength(nivel_texto, font=font_xp)) - int(16 * escala), barra_y), 
              nivel_texto, font=font_xp, fill="white")
    
    fundo = Image.new("RGBA", (barra_largura, barra_altura), (100, 100, 100, 180))
    fundo_mask = Image.new("L", (barra_largura, barra_altura), 0)
    ImageDraw.Draw(fundo_mask).rounded_rectangle((0, 0, barra_largura, barra_altura), radius=10, fill=255)
    bg.paste(fundo, (barra_x, barra_y), fundo_mask)
    
    if barra_cheia > 0:
        preenchida = Image.new("RGBA", (barra_cheia, barra_altura), ImageColor.getrgb(cor_barra))
        preenchida_mask = Image.new("L", (barra_cheia, barra_altura), 0)
        ImageDraw.Draw(preenchida_mask).rounded_rectangle((0, 0, barra_cheia, barra_altura), radius=10, fill=255)
        bg.paste(preenchida, (barra_x, barra_y), preenchida_mask)
    
    draw.rounded_rectangle((barra_x, barra_y, barra_x + barra_largura, barra_y + barra_altura), 
                          radius=10, outline="white", width=2)

def desenhar_barra_xp_layout2(bg, draw, nivel, restante_xp, cor_barra, cor_texto, 
                              info_x, centro_y, barra_largura, barra_altura, font_xp):
    progresso = min(restante_xp / 1000, 1.0)
    barra_cheia = int(barra_largura * progresso)
    
    try:
        cor_rgb = ImageColor.getrgb(cor_barra)
    except:
        cor_rgb = (100, 180, 255)
    
    barra_x = info_x
    barra_y = centro_y + 2
    
    fundo = Image.new("RGBA", (barra_largura, barra_altura), (100, 100, 100, 180))
    fundo_mask = Image.new("L", (barra_largura, barra_altura), 0)
    ImageDraw.Draw(fundo_mask).rounded_rectangle((0, 0, barra_largura, barra_altura), radius=10, fill=255)
    bg.paste(fundo, (barra_x, barra_y), fundo_mask)
    
    if barra_cheia > 0:
        preenchida = Image.new("RGBA", (barra_cheia, barra_altura), cor_rgb)
        preenchida_mask = Image.new("L", (barra_cheia, barra_altura), 0)
        ImageDraw.Draw(preenchida_mask).rounded_rectangle((0, 0, barra_cheia, barra_altura), radius=10, fill=255)
        bg.paste(preenchida, (barra_x, barra_y), preenchida_mask)
    
    draw.rounded_rectangle((barra_x, barra_y, barra_x + barra_largura, barra_y + barra_altura), 
                          radius=10, outline=cor_texto, width=2)
    
    draw.text((barra_x, barra_y + barra_altura + 6), 
              f"Nível {nivel} | XP {restante_xp}/1000", 
              font=font_xp, fill=cor_texto)

def desenhar_casamento(bg, draw, user, parceiro, faixa_y, escala, font):
    nome1 = limpar_unicode(user.display_name)
    nome2 = limpar_unicode(parceiro.display_name)
    texto = f"{nome1} é casado com {nome2}"
    
    text_x = int(210 * escala)
    text_y = faixa_y + int(102 * escala)
    draw.text((text_x, text_y), texto, font=font, fill="white")
    
    try:
        coracao = Image.open("assets/amor.png").convert("RGBA")
        emoji_size = int(28 * escala)
        coracao = coracao.resize((emoji_size, emoji_size), Image.LANCZOS)
        
        emoji_y = text_y + 2
        bg.paste(coracao, (text_x - emoji_size - 6, emoji_y), coracao)
        bg.paste(coracao, (text_x + int(draw.textlength(texto, font=font)) + 6, emoji_y), coracao)
    except Exception as e:
        logging.warning(f"Erro ao carregar coração.png: {e}")

def desenhar_casamento_xp(bg, draw, user, parceiro, barra_x, barra_y, barra_altura, font):
    nome1 = limpar_unicode(user.display_name)
    nome2 = limpar_unicode(parceiro.display_name)
    texto = f"{nome1} é casado com {nome2}"
    
    text_x = barra_x + 34
    text_y = barra_y + barra_altura + 27
    draw.text((text_x, text_y), texto, font=font, fill="white")
    
    try:
        coracao = Image.open("assets/amor.png").convert("RGBA")
        emoji_size = 24
        coracao = coracao.resize((emoji_size, emoji_size), Image.LANCZOS)
        
        emoji_y = text_y
        bg.paste(coracao, (barra_x, emoji_y), coracao)
        bg.paste(coracao, (text_x + int(draw.textlength(texto, font=font)) + 6, emoji_y), coracao)
    except Exception as e:
        logging.warning(f"Erro ao carregar coração.png: {e}")

def desenhar_badges(bg, badge_imgs, faixa_y, escala):
    spacing = int(8 * escala)
    badge_size = int(32 * escala)
    total_width = len(badge_imgs) * (badge_size + spacing)
    x_start = bg.width - total_width - int(70 * escala)
    y_start = faixa_y + int(10 * escala)
    
    for i, badge in enumerate(badge_imgs):
        bg.paste(badge, (x_start + i * (badge_size + spacing), y_start), badge)

def desenhar_badges_xp(bg, badge_imgs, largura):
    total_badges = len(badge_imgs)
    badge_x = largura - (total_badges * 36) - 25
    badge_y = 30
    
    for i, badge in enumerate(badge_imgs):
        bg.paste(badge, (badge_x + i * 36, badge_y), badge)

# =========================
# FUNÇÕES DE CARREGAMENTO DE FUNDO
# =========================

async def carregar_fundo_perfil(user, largura, altura, cfg):
    bg_path = f"fundos/{user.id}.png"
    
    try:
        if cfg.get("background"):
            resp = requests.get(cfg["background"], timeout=10)
            if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/"):
                with open(bg_path, "wb") as f:
                    f.write(resp.content)
        bg = Image.open(bg_path).convert("RGBA").resize((largura, altura))
    except:
        try:
            bg = Image.open("assets/default_bg.png").convert("RGBA").resize((largura, altura))
        except:
            bg = Image.new("RGBA", (largura, altura), cfg.get("color", "#2F3136"))
    
    return bg

async def carregar_fundo_xp(user, largura, altura):
    try:
        bg = Image.open(f'fundos_xp/{user.id}.png').convert('RGBA').resize((largura, altura))
    except:
        try:
            bg = Image.open("assets/banner_bg.webp").convert("RGBA").resize((largura, altura))
        except:
            bg = Image.new("RGBA", (largura, altura), (20, 20, 20, 255))
    return bg

async def carregar_fundo_gif(user, largura, altura, cfg):
    bg_path = f"fundos/{user.id}.gif"
    
    try:
        if cfg.get("background"):
            resp = requests.get(cfg["background"], timeout=10)
            if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("image/"):
                with open(bg_path, "wb") as f:
                    f.write(resp.content)
        bg = Image.open(bg_path)
    except:
        try:
            bg = Image.open("assets/default_bg.png")
        except:
            bg = Image.new("RGBA", (largura, altura), cfg.get("color", "#2F3136"))
    
    return bg

def salvar_imagem(imagem):
    """Salva a imagem em um buffer."""
    buffer = BytesIO()
    imagem.save(buffer, "PNG")
    buffer.seek(0)
    return buffer

def salvar_gif(frames, gif_original=None):
    buffer = BytesIO()
    
    if len(frames) > 1:
        duration = gif_original.info.get('duration', 100) if gif_original else 100
        frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:],
                       duration=duration, loop=0, optimize=False)
    else:
        frames[0].save(buffer, format="PNG", optimize=True)
    
    buffer.seek(0)
    return buffer