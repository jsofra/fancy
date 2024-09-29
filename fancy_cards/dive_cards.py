import itertools

from PIL import Image, ImageDraw
import pandas as pd
import numpy as np


def interpose_list(l, item):
    items = list(itertools.repeat(item, len(l)-1))
    interposed = l + items
    interposed[::2] = l 
    interposed[1::2] = items
    return interposed


def paste_centred(paste_to, paste_from, centre_at):
    c_x, c_y = centre_at
    paste_to.paste(paste_from, (c_x - int(paste_from.width/2), c_y - int(paste_from.height/2)))


def draw_border(draw, card, colour):

    draw.rounded_rectangle(
        [(0, 0), card.size],
        outline=colour,
        width=20,
    )

    draw.rounded_rectangle(
        [(10, 10), (card.size[0]-10, card.size[1]-10)],
        radius=30,
        outline="white",
        width=20,
        corners=(True, True, True, True)
    )


def create_dive_image(images, dive, border_colour):
    card = images["template"].copy()
    draw = ImageDraw.Draw(card)

    draw_border(draw, card, border_colour)

    draw.text((20, 20), dive["group"], font_size=52, fill="#0146FF")
    draw.text((100, 80), dive["sub_group"], font_size=42, fill="#FF0000")

    rot_y = 250
    and_y = 400
    positions_y = 550

    is_not_free_dive = dive.isna()["free"]

    draw.text(
        (int(card.width/2), and_y),
        "and" if is_not_free_dive else "and any 2 of",
        font_size=52,
        fill="#00DDFF",
        anchor="mm"
    )

    rotations = dive[["som", "twist"]].dropna()

    rot_items = interpose_list(list(rotations.items()), ("plus", None))
    rotations_spacing = int(card.width/(len(rot_items)+1))

    rot_colours = {
        "som": "#FF7C00",
        "twist": "#CE00FF",
    }

    for (idx, (rot_name, rot_count)) in enumerate(rot_items):
        rot_pos = ((idx+1)*rotations_spacing, rot_y)

        paste_centred(card, images[rot_name], rot_pos)
        if rot_count is not None:
            draw.text(
                rot_pos,
                str(rot_count).replace(".0", ""),
                font_size=52,
                fill=rot_colours[rot_name],
                anchor="mm"
            )

    if is_not_free_dive:
        positions = dive[["str", "pike", "tuck"]].dropna()
    else:
        dive["pike"] = dive["free"]
        positions = dive[["str", "pike", "tuck"]].replace({np.nan: None})
        draw.text((300, 20), "(Free dive)", font_size=42, fill="#05AF00")

    position_items = interpose_list(list(positions.items()), ("or", None))
    positions_spacing = int(card.width/(len(position_items)+1))

    for (idx, (pos_name, pos_dd)) in enumerate(position_items):
        paste_centred(card, images[pos_name], ((idx+1)*positions_spacing, positions_y))
        if pos_dd is not None:
            draw.text(
                ((idx+1)*positions_spacing, positions_y + 150),
                str(pos_dd),
                font_size=58,
                fill="#05AF00",
                anchor="mm"
            )

    return card


def generate_dive_cards(
    base_dir: str,
    dives: pd.DataFrame,
    border_colour
):

    som_img = Image.open(base_dir + "som.jpg")
    twist_img = Image.open(base_dir + "twist.jpg")
    str_img = Image.open(base_dir + "str.jpg")
    pike_img = Image.open(base_dir + "pike.jpg")
    tuck_img = Image.open(base_dir + "tuck.jpg")
    plus_img = Image.open(base_dir + "plus.jpg")
    or_img = Image.open(base_dir + "or.jpg")

    card_w = 515
    card_h = 800

    template = Image.new("RGB", (card_w, card_h), (255, 255, 255, 255))

    images = {
        "template": template,
        "som": som_img,
        "twist": twist_img,
        "str": str_img,
        "pike": pike_img,
        "tuck": tuck_img,
        "plus": plus_img,
        "or": or_img,
    }

    dives = dives.copy(deep=True)

    card_imgs = []

    for _, dive in dives.iterrows():
        card_imgs.append(create_dive_image(images, dive, border_colour))

    dives["PIL"] = card_imgs

    return dives


def write_images(output_dir: str, cards: pd.DataFrame, name: str, base_url: str):

    cards = cards.copy(deep=True)

    file_names = []

    for idx, card in cards.iterrows():
        file_name = f"{name}_{idx}.jpg"
        card["PIL"].save(output_dir + file_name, format='JPEG', quality=75)
        file_names.append(base_url + file_name)
    
    cards["image"] = file_names

    return cards