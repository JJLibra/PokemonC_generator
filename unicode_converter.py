import os
import numpy as np
from PIL import Image, UnidentifiedImageError
import config

def get_reset_escape_code():
    return '\033[0m'

def get_color_escape_code(r, g, b, background=False):
    if background:
        return f'\033[48;2;{r};{g};{b}m' if background else f'\033[38;2;{r};{g};{b}m'
    else:
        return f'\033[38;2;{r};{g};{b}m'

class SmallConverter:
    def __init__(self, image: Image.Image):
        self._image = image

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, value):
        self._image = value

    def crop_to_content(self) -> None:
        """Remove padding around the image. Uses alpha channel to find padding"""
        image_array = np.array(self.image)

        alpha_channel = image_array[:, :, 3]
        non_zero_x_values, non_zero_y_values = alpha_channel.nonzero()
        top, left = np.min(non_zero_x_values), np.min(non_zero_y_values)
        bottom, right = np.max(non_zero_x_values), np.max(non_zero_y_values)
        cropped_image = image_array[top : bottom + 1, left : right + 1]

        self._image = Image.fromarray(cropped_image)

    def convert_to_rgba(self) -> None:
        if self.image.mode != "RGBA":
            rgba_image = self.image.convert("RGBA")
            self._image = rgba_image

    def convert_image_to_unicode(self) -> str:
        upper_block = "▀"
        lower_block = "▄"
        empty_block = " "

        unicode_sprite = ""

        image_array = np.array(self.image)
        height, width, channels = image_array.shape

        if height % 2:
            padded_array = np.zeros((height + 1, width, channels)).astype(np.uint8)
            padded_array[:height, :, :] = image_array
            height, width, channels = padded_array.shape
            image_array = padded_array

        reset_code = get_reset_escape_code()
        for i in range(0, height, 2):
            for j in range(width):
                upper_pixel = image_array[i, j]
                lower_pixel = image_array[i + 1, j]
                if upper_pixel[3] == 0 and lower_pixel[3] == 0:
                    unicode_sprite += empty_block
                elif upper_pixel[3] == 0:
                    r, g, b = lower_pixel[:3]
                    escape_code = get_color_escape_code(r, g, b)
                    unicode_sprite += escape_code + lower_block + reset_code
                elif lower_pixel[3] == 0:
                    r, g, b = upper_pixel[:3]
                    escape_code = get_color_escape_code(r, g, b)
                    unicode_sprite += escape_code + upper_block + reset_code
                else:
                    r_f, g_f, b_f = upper_pixel[:3]
                    r_b, g_b, b_b = lower_pixel[:3]
                    foreground_escape = get_color_escape_code(r_f, g_f, b_f)
                    background_escape = get_color_escape_code(r_b, g_b, b_b, background=True)
                    unicode_sprite += foreground_escape + background_escape + upper_block + reset_code
            unicode_sprite += "\n"
        unicode_sprite += reset_code

        return unicode_sprite

def image_to_ansi(image_path, max_width=80, size_scale=1.0):
    try:
        img = Image.open(image_path)
    except (UnidentifiedImageError, IOError) as e:
        print(f"Unable to open image file {image_path}: {e}")
        return None

    converter = SmallConverter(img)
    converter.convert_to_rgba()
    converter.crop_to_content()

    width, height = converter.image.size
    aspect_ratio = height / width
    new_width = int(max_width * size_scale)  # Scale the width based on the size_scale parameter
    new_height = int(aspect_ratio * new_width)
    converter.image = converter.image.resize((new_width, new_height))

    ansi_art = converter.convert_image_to_unicode()

    return ansi_art

def process_folder(folder_path, save_file_path, size_scale=1.0):
    for filename in os.listdir(folder_path):
        if filename.endswith('.png'):
            image_path = os.path.join(folder_path, filename)
            ansi_art = image_to_ansi(image_path, size_scale=size_scale)
            if ansi_art is None:
                continue
            txt_filename = os.path.splitext(filename)[0]
            txt_path = os.path.join(save_file_path, txt_filename)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(ansi_art)

if __name__ == '__main__':
    base_folder = config.Images_path
    large_save_folder = config.Large_Ansi_path
    small_save_folder = config.Small_Ansi_path
    image_types = ['back', 'back_shiny', 'front', 'front_shiny']

    for image_type in image_types:
        folder_path = os.path.join(base_folder, image_type)
        large_file_path = os.path.join(large_save_folder, image_type)
        small_file_path = os.path.join(small_save_folder, image_type)

        if not os.path.exists(large_file_path):
            os.makedirs(large_file_path)
        if not os.path.exists(small_file_path):
            os.makedirs(small_file_path)

        if os.path.exists(folder_path):
            process_folder(folder_path, large_file_path, size_scale=1.0)  # Larger scale
            process_folder(folder_path, small_file_path, size_scale=0.5)  # Smaller scale
        else:
            print(f"Folder: {folder_path} does not exist.")
