import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
import paths
from ... import config_file as cfg


class SpeechBubble(object):
    """
    A class to represent the metadata to render a speech bubble

    :param texts: A list of texts from the text corpus to render in this
    bubble

    :type texts: lists

    :param text_indices: The indices of the text from the dataframe
    for easy retrival

    :type text_indices: lists

    :param font: The path to the font used in the bubble

    :type font: str

    :param speech_bubble: The path to the base speech bubble file
    used for this bubble

    :type speech_bubble: str

    :param writing_areas: The areas within the bubble where it is okay
    to render text

    :type writing_areas: list

    :param resize_to: The amount of area this text bubble should consist of
    which is a ratio of the panel's area

    :type resize_to: float

    :param location: The location of the top left corner of the speech bubble
    on the page

    :type location: list

    :param width: Width of the speech bubble

    :type width: float

    :param height: Height of the speech bubble

    :type height: float

    :param transforms: A list of transformations to change
    the shape of the speech bubble

    :type transforms: list, optional

    :param transform_metadata: Metadata associated with transformations,
    defaults to None

    :type transform_metadata: dict, optional

    :param text_orientation: Whether the text of this speech bubble
    is written left to right ot top to bottom

    :type text_orientation: str, optional
    """

    def __init__(self,
                 texts,
                 text_indices,
                 font,
                 speech_bubble,
                 writing_areas,
                 location,
                 width,
                 height,
                 language=paths.ENGLISH_LANGUAGE,
                 transforms=None,
                 transform_metadata=None,
                 text_orientation="ltr"):
        """
        Constructor method
        """

        self.texts = texts
        self.language = language
        # Index of dataframe for the text
        self.text_indices = text_indices
        self.font = font
        self.speech_bubble = speech_bubble
        self.writing_areas = writing_areas

        # Location on panel
        self.location = location
        self.width = width
        self.height = height

        self.transform_metadata = {}
        if transform_metadata is not None:
            self.transform_metadata = transform_metadata

        if transforms is None:
            possible_transforms = [
                "flip horizontal",
                "flip vertical",
                "rotate",
                "stretch x",
                "stretch y",
            ]
            # 1 in 50 chance of no transformation
            if np.random.rand() < 0.98:
                self.transforms = list(np.random.choice(
                    possible_transforms,
                    2
                )
                )

                # 1 in 20 chance of inversion
                if np.random.rand() < 0.05:
                    self.transforms.append("invert")

                if "stretch x" in self.transforms:
                    # Up to 30% stretching
                    factor = np.random.random()*0.3
                    self.transform_metadata["stretch_x_factor"] = factor
                if "stretch y" in self.transforms:
                    factor = np.random.random()*0.3
                    self.transform_metadata["stretch_y_factor"] = factor

                if "rotate" in self.transforms:
                    rotation = np.random.randint(10, 30)
                    self.transform_metadata["rotation_amount"] = rotation

            else:
                self.transforms = []
        else:
            self.transforms = transforms

        if text_orientation is None:
            # 1 in 100 chance
            if np.random.random() < 0.01:
                self.text_orientation = "ltr"
            else:
                self.text_orientation = "ttb"
        else:
            self.text_orientation = text_orientation

        min_font_size = cfg.min_font_size
        max_font_size = cfg.max_font_size
        self.font_size = np.random.randint(min_font_size,
                                           max_font_size
                                           )

    def dump_data(self):
        """
        A method to take all the SpeechBubble's relevant data
        and create a dictionary out of it so it can be
        exported to JSON via the Page(Panel) class's
        dump_data method

        :return: Data to be returned to Page(Panel) class's
        dump_data method
        :rtype: dict
        """
        data = dict(
            texts=self.texts,
            text_indices=self.text_indices,
            font=self.font,
            font_size=self.font_size,
            speech_bubble=self.speech_bubble,
            writing_areas=self.writing_areas,
            location=self.location,
            width=self.width,
            height=self.height,
            transforms=self.transforms,
            transform_metadata=self.transform_metadata,
            text_orientation=self.text_orientation
        )

        return data

    def render(self):
        """
        A function to render this speech bubble

        :return: A list of states of the speech bubble,
        the speech bubble itself, it's mask and it's location
        on the page
        :rtype: tuple
        """

        bubble = Image.open(self.speech_bubble).convert("RGBA")
        mask = bubble.copy()

        # Set variable font size
        # current_font_size = self.font_size
        # font = ImageFont.truetype(self.font, current_font_size)

        # States is used to indicate whether this bubble is
        # inverted or not to the page render function
        transforms_applied = []

        # Pre-rendering transforms
        for transform in self.transforms:
            if transform == "invert":
                if bubble.mode == 'RGBA':
                    r, g, b, a = bubble.split()
                    rgb_image = Image.merge('RGB', (r, g, b))
                    inverted_image = ImageOps.invert(rgb_image)
                    r2, g2, b2 = inverted_image.split()
                    bubble = Image.merge('RGBA', (r2, g2, b2, a))
                else:
                    bubble = ImageOps.invert(bubble)
                transforms_applied.append("inverted")

            # elif transform == "flip vertical":
            #     bubble = ImageOps.flip(bubble)
            #     mask = ImageOps.flip(mask)
            #     # TODO: vertically flip box coordinates
            #     new_writing_areas = []
            #     for area in self.writing_areas:
            #         og_height = area['original_height']

            #         # Convert from percentage to actual values
            #         px_height = (area['height']/100)*og_height

            #         og_y = ((area['y']/100)*og_height)
            #         cydist = abs(cy - og_y)
            #         new_y = (2*cydist + og_y) - px_height
            #         new_y = (new_y/og_height)*100
            #         area['y'] = new_y
            #         new_writing_areas.append(area)

            #     self.writing_areas = new_writing_areas
            #     transforms_applied.append("vflip")

            # elif transform == "flip horizontal":
            #     bubble = ImageOps.mirror(bubble)
            #     mask = ImageOps.mirror(mask)
            #     new_writing_areas = []
            #     for area in self.writing_areas:
            #         og_width = area['original_width']

            #         # Convert from percentage to actual values
            #         px_width = (area['width']/100)*og_width

            #         og_x = ((area['x']/100)*og_width)
            #         # og_y = ((area['y']/100)*og_height)
            #         cxdist = abs(cx - og_x)
            #         new_x = (2*cxdist + og_x) - px_width
            #         new_x = (new_x/og_width)*100
            #         area['x'] = new_x
            #         new_writing_areas.append(area)

            #     self.writing_areas = new_writing_areas
            #     transforms_applied.append("hflip")

            # elif transform == "stretch x":

            #     stretch_factor = self.transform_metadata['stretch_x_factor']
            #     new_size = (round(w*(1+stretch_factor)), h)
            #     # Reassign for resizing later
            #     w, h = new_size
            #     bubble = bubble.resize(new_size)
            #     mask = mask.resize(new_size)

            #     new_writing_areas = []
            #     for area in self.writing_areas:
            #         og_width = area['original_width']

            #         # Convert from percentage to actual values
            #         px_width = (area['width']/100)*og_width

            #         area['original_width'] = og_width*(1+stretch_factor)

            #         new_writing_areas.append(area)

            #     self.writing_areas = new_writing_areas
            #     transforms_applied.append("xstretch")

            # elif transform == "stretch y":
            #     stretch_factor = self.transform_metadata['stretch_y_factor']
            #     new_size = (w, round(h*(1+stretch_factor)))

            #     # Reassign for resizing later
            #     w, h = new_size
            #     bubble = bubble.resize(new_size)
            #     mask = mask.resize(new_size)

            #     new_writing_areas = []
            #     for area in self.writing_areas:
            #         og_height = area['original_height']

            #         # Convert from percentage to actual values
            #         px_height = (area['height']/100)*og_height

            #         area['original_height'] = og_height*(1+stretch_factor)

            #         new_writing_areas.append(area)

            #     self.writing_areas = new_writing_areas
            #     transforms_applied.append("ystretch")

        if "inverted" in transforms_applied:
            fill_type = "white"
        else:
            fill_type = "black"

        # Draw text into bubble
        for _, area in enumerate(self.writing_areas):
            # Create context boundary box
            padding = cfg.bubble_content_padding
            width, height = area["width"] - padding, area["height"] - padding
            x1, y1 = area["x"] + padding, area["y"] + padding

            if width > 0 and height > 0:
                empty_image = Image.new(mode="RGBA", size=(width, height))
                draw = ImageDraw.Draw(empty_image)

                # Get text lines (It splits text into lines)
                text = self.texts[0][self.language]
                if self.language == paths.JAPANASE_LANGUAGE:
                    text = text + text + text + text

                # Wrap text for 16 chars per line
                text_segmented = textwrap.wrap(text, width=16)
                text = "\n".join(text_segmented)

                # Scale font size horizontally
                current_font_size = cfg.min_font_size
                font = ImageFont.truetype(self.font, current_font_size)
                current_font_size = (
                    width / draw.textsize(text, font=font)[0]) * current_font_size
                current_font_size = round(current_font_size)
                current_font_size = max(
                    min(current_font_size, cfg.max_font_size), cfg.min_font_size)
                font = ImageFont.truetype(self.font, current_font_size)

                # Center text
                w, h = draw.textsize(text, font=font)
                x = max(round((width - w) / 2), 0)
                y = max(round((height - h) / 2), 0)

                # Write text inside bubble
                draw.text((x, y), text,
                          #   direction=self.text_orientation
                          align='center',
                          font=font,
                          fill=fill_type)

                bubble.paste(empty_image, (x1, y1), empty_image)

        # Resize bubble
        bubble = bubble.resize((self.width, self.height))
        mask = mask.resize((self.width, self.height))

        # Perform rotation if it was in transforms
        if "rotate" in self.transforms:
            rotation = self.transform_metadata['rotation_amount']
            bubble = bubble.rotate(rotation, Image.NEAREST, expand=1)
            mask = mask.rotate(rotation, Image.NEAREST, expand=1)

        return bubble, self.location
