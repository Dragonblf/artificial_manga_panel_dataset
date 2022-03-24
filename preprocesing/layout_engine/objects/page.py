import numpy as np
from PIL import Image, ImageDraw
import json
import uuid
from ..helpers import crop_image_only_outside_rows_columns, crop_image_only_outside, get_leaf_panels
from ... import config_file as cfg
from .panel import Panel
from .speech_bubble import SpeechBubble


class Page(Panel):
    """
    A class that represents a full page consiting of multiple child panels

    :param coords: A list of the boundary coordinates of a page

    :type coords: list

    :param page_type: Signifies whether a page consists of vertical
    or horizontal panels or both

    :type page_type: str

    :param num_panels: Number of panels in this page

    :type num_panels: int

    :param children: List of direct child panels of this page

    :type children: list, optional:
    """

    def __init__(self,
                 coords=[],
                 page_type="",
                 num_panels=1,
                 children=[],
                 name=None
                 ):
        """
        Constructor method
        """

        if len(coords) < 1:
            topleft = (0.0, 0.0)
            topright = (cfg.page_width, 0.0)
            bottomleft = (0.0, cfg.page_height)
            bottomright = cfg.page_size
            coords = [
                topleft,
                topright,
                bottomright,
                bottomleft
            ]

        if name is None:
            self.name = str(uuid.uuid1())
        else:
            self.name = name

        # Initalize the panel super class
        super().__init__(coords=coords,
                         name=self.name,
                         parent=None,
                         orientation=None,
                         children=[]
                         )

        self.num_panels = num_panels
        self.page_type = page_type

        # Whether this page needs to be rendered with a background
        self.background = None

        # The leaf children of tree of panels
        # These are the panels that are actually rendered
        self.leaf_children = []

        # Size of the page
        self.page_size = cfg.page_size

    def dump_data(self, dataset_path, dry=True):
        """
        A method to take all the Page's relevant data
        and create a dictionary out of it so it can be
        exported to JSON so that it can then be loaded
        and rendered to images in parallel

        :param dataset_path: Where to dump the JSON file

        :type dataset_path: str

        :param dry: Whether to just return or write the JSON file

        :type dry: bool, optional

        :return: Optional return when running dry of a json data dump
        :rtype: str
        """

        # Recursively dump children
        if len(self.children) > 0:
            children_rec = [child.dump_data() for child in self.children]
        else:
            children_rec = []

        speech_bubbles = [bubble.dump_data() for bubble in self.speech_bubbles]
        data = dict(
            name=self.name,
            num_panels=int(self.num_panels),
            page_type=self.page_type,
            page_size=self.page_size,
            background=self.background,
            children=children_rec,
            speech_bubbles=speech_bubbles
        )

        if not dry:
            with open(dataset_path + self.name + cfg.metadata_format, "w+") as json_file:
                json.dump(data, json_file, indent=2)
        else:
            return json.dumps(data, indent=2)

    def load_data(self, filename):
        """
        This method reverses the dump_data function and
        load's the metadata of the page from the JSON
        file that has been loaded.

        :param filename: JSON filename to load

        :type filename: str
        """
        with open(filename, "rb") as json_file:

            data = json.load(json_file)

            self.name = data['name']
            self.num_panels = int(data['num_panels'])
            self.page_type = data['page_type']
            self.background = data['background']

            if len(data['speech_bubbles']) > 0:
                for speech_bubble in data['speech_bubbles']:
                    # Line constraints
                    text_orientation = speech_bubble['text_orientation']
                    transform_metadata = speech_bubble['transform_metadata']
                    bubble = SpeechBubble(
                        texts=speech_bubble['texts'],
                        text_indices=speech_bubble['text_indices'],
                        font=speech_bubble['font'],
                        speech_bubble=speech_bubble['speech_bubble'],
                        writing_areas=speech_bubble['writing_areas'],
                        resize_to=speech_bubble['resize_to'],
                        location=speech_bubble['location'],
                        width=speech_bubble['width'],
                        height=speech_bubble['height'],
                        transforms=speech_bubble['transforms'],
                        transform_metadata=transform_metadata,
                        text_orientation=text_orientation
                    )

                    self.speech_bubbles.append(bubble)

            # Recursively load children
            if len(data['children']) > 0:
                for child in data['children']:
                    panel = Panel(
                        coords=child['coordinates'],
                        name=child['name'],
                        parent=self,
                        orientation=child['orientation'],
                        non_rect=child['non_rect']
                    )
                    panel.load_data(child)
                    self.children.append(panel)

    def render(self, show=False):
        """
        A function to render this page to an image

        :param show: Whether to return this image or to show it

        :type show: bool, optional
        """

        leaf_children = []
        if self.num_panels > 1:
            # Get all the panels to be rendered
            if len(self.leaf_children) < 1:
                get_leaf_panels(self, leaf_children)
            else:
                leaf_children = self.leaf_children

        W = cfg.page_width
        H = cfg.page_height

        # Create a new blank image
        page_img = Image.new(size=(W, H), mode="RGBA", color="white")
        draw_rect = ImageDraw.Draw(page_img)

        # Set background if needed
        if self.background is not None:
            bg = Image.open(self.background).convert("L")
            img_array = np.asarray(bg)
            crop_array = crop_image_only_outside(img_array)
            bg = Image.fromarray(crop_array)
            bg = bg.resize((W, H))
            page_img.paste(bg, (0, 0))

        # Render panels
        for panel in leaf_children:

            # Panel coords
            rect = panel.get_polygon()

            # Open the illustration to put within panel
            if panel.image is not None:
                img = Image.open(panel.image)

                # Clean it up by cropping the black areas
                img_array = np.asarray(img)
                crop_array = crop_image_only_outside(img_array)

                img = Image.fromarray(crop_array)

                # Resize it to the page's size as a simple
                # way to crop differnt parts of it

                # TODO: Figure out how to do different types of
                # image crops for smaller panels
                w_rev_ratio = cfg.page_width/img.size[0]
                h_rev_ratio = cfg.page_height/img.size[1]

                img = img.resize(
                    (round(img.size[0]*w_rev_ratio),
                     round(img.size[1]*h_rev_ratio))
                )

                # Create a mask for the panel illustration
                mask = Image.new("L", cfg.page_size, 0)
                draw_mask = ImageDraw.Draw(mask)

                # On the mask draw and therefore cut out the panel's
                # area so that the illustration can be fit into
                # the page itself
                draw_mask.polygon(rect, fill=255)

            # Draw outline
            draw_rect.line(rect, fill="black", width=cfg.boundary_width)

            # Paste illustration onto the page
            if panel.image is not None:
                page_img.paste(img, (0, 0), mask)

        # If it's a single panel page
        if self.num_panels < 2:
            leaf_children.append(self)

        # Render bubbles
        for panel in leaf_children:
            if len(panel.speech_bubbles) < 1:
                continue
            # For each bubble
            for sb in panel.speech_bubbles:
                bubble, location = sb.render()
                page_img.paste(bubble, location, bubble)

        if show:
            page_img.show()
        else:
            return page_img

    def renderColored(self, show=False):
        """
        A function to render this page to an image

        :param show: Whether to return this image or to show it

        :type show: bool, optional
        """

        leaf_children = []
        if self.num_panels > 1:
            # Get all the panels to be rendered
            if len(self.leaf_children) < 1:
                get_leaf_panels(self, leaf_children)
            else:
                leaf_children = self.leaf_children

        W = cfg.page_width
        H = cfg.page_height

        # Create a new blank image
        page_img = Image.new(size=(W, H), mode="RGBA", color="white")
        draw_rect = ImageDraw.Draw(page_img)

        # Set background if needed
        if self.background is not None:
            bg = Image.open(self.background).convert("L")
            img_array = np.asarray(bg)
            crop_array = crop_image_only_outside(img_array)
            bg = Image.fromarray(crop_array)
            bg = bg.resize((W, H))
            page_img.paste(bg, (0, 0))

        # Render panels
        for panel in leaf_children:

            # Panel coords
            rect = panel.get_polygon()

            # Open the illustration to put within panel
            if panel.image is not None:
                imgBW = Image.open(panel.image)
                imgColored = Image.open(panel.get_colored_image())

                # Clean it up by cropping the black areas
                img_array = np.asarray(imgBW)
                col_start, col_end, row_start, row_end = crop_image_only_outside_rows_columns(img_array)
                img = imgColored.crop((col_start, row_start, col_end, row_end))

                # Resize it to the page's size as a simple
                # way to crop differnt parts of it

                # TODO: Figure out how to do different types of
                # image crops for smaller panels
                w_rev_ratio = cfg.page_width/img.size[0]
                h_rev_ratio = cfg.page_height/img.size[1]

                img = img.resize(
                    (round(img.size[0]*w_rev_ratio),
                     round(img.size[1]*h_rev_ratio))
                )

                # Create a mask for the panel illustration
                mask = Image.new("L", cfg.page_size, 0)
                draw_mask = ImageDraw.Draw(mask)

                # On the mask draw and therefore cut out the panel's
                # area so that the illustration can be fit into
                # the page itself
                draw_mask.polygon(rect, fill=255)

            # Draw outline
            draw_rect.line(rect, fill="black", width=cfg.boundary_width)

            # Paste illustration onto the page
            if panel.image is not None:
                page_img.paste(img, (0, 0), mask)

        # If it's a single panel page
        if self.num_panels < 2:
            leaf_children.append(self)

        # Render bubbles
        for panel in leaf_children:
            if len(panel.speech_bubbles) < 1:
                continue
            # For each bubble
            for sb in panel.speech_bubbles:
                bubble, location = sb.render()
                page_img.paste(bubble, location, bubble)

        if show:
            page_img.show()
        else:
            return page_img
