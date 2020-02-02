# Standard Library Imports
from pathlib import Path
from typing import Optional

# Third Party Imports
import PIL.Image as PilImage
from pydantic import FilePath
from pydantic import StrictInt
from pydantic import root_validator

# Project Imports
from hyperglass.configuration.models._utils import HyperglassModel


class OpenGraph(HyperglassModel):
    """Validation model for params.opengraph."""

    width: Optional[StrictInt]
    height: Optional[StrictInt]
    image: Optional[FilePath]

    @root_validator
    def validate_image(cls, values):
        """Set default opengraph image location.

        Arguments:
            value {FilePath} -- Path to opengraph image file.

        Returns:
            {Path} -- Opengraph image file path object
        """
        supported_extensions = (".jpg", ".jpeg", ".png")
        if (
            values["image"].suffix is not None
            and values["image"] not in supported_extensions
        ):
            raise ValueError(
                "OpenGraph image must be one of {e}".format(
                    e=", ".join(supported_extensions)
                )
            )
        if values["image"] is None:
            image = (
                Path(__file__).parent.parent.parent
                / "static/images/hyperglass-opengraph.png"
            )
            values["image"] = "".join(str(image).split("static")[1::])

        with PilImage.open(image) as img:
            width, height = img.size
            if values["width"] is None:
                values["width"] = width
            if values["height"] is None:
                values["height"] = height

        return values

    class Config:
        """Pydantic model configuration."""

        title = "OpenGraph"
        description = "OpenGraph configuration parameters"
        fields = {
            "width": {
                "title": "Width",
                "description": "Width of OpenGraph image. If unset, the width will be automatically derived by reading the image file.",
            },
            "height": {
                "title": "Height",
                "description": "Height of OpenGraph image. If unset, the height will be automatically derived by reading the image file.",
            },
            "image": {
                "title": "Image File",
                "description": "Valid path to a JPG or PNG file to use as the OpenGraph image.",
            },
        }
