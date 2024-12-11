import os
from pathlib import Path
from typing import List, Optional, Tuple

import itk
import numpy as np
import numpy.typing as npt
from brainglobe_atlasapi import BrainGlobeAtlas
from tifffile import imwrite


def get_atlas_by_name(atlas_name: str) -> BrainGlobeAtlas:
    """
    Get a BrainGlobeAtlas object by its name.

    Parameters
    ----------
    atlas_name : str
        The name of the atlas.

    Returns
    -------
    BrainGlobeAtlas
        The BrainGlobeAtlas object.
    """
    atlas = BrainGlobeAtlas(atlas_name)

    return atlas


def run_registration(
    atlas_image,
    moving_image,
    annotation_image,
    parameter_lists: List[Tuple[str, dict]],
    output_directory: Optional[Path] = None,
) -> Tuple[npt.NDArray, itk.ParameterObject, npt.NDArray, npt.NDArray]:
    """
    Run the registration process on the given images.

    Parameters
    ----------
    atlas_image : npt.NDArray
        The atlas image.
    moving_image : npt.NDArray
        The moving image.
    annotation_image : npt.NDArray
        The annotation image.
    parameter_lists : List[tuple[str, dict]]
        The list of registration parameters, one for each transform.
    output_directory : Optional[Path], optional
        The output directory for the registration results, by default None

    Returns
    -------
    npt.NDArray
        The result image.
    itk.ParameterObject
        The result transform parameters.
    npt.NDArray
        The transformed annotation image.
    npt.NDArray
        The deformation field.
    """
    # convert to ITK, view only
    atlas_image = itk.GetImageViewFromArray(atlas_image).astype(itk.F)
    moving_image = itk.GetImageViewFromArray(moving_image).astype(itk.F)

    # This syntax needed for 3D images
    elastix_object = itk.ElastixRegistrationMethod.New(
        moving_image, atlas_image
    )

    parameter_object = setup_parameter_object(parameter_lists=parameter_lists)

    elastix_object.SetParameterObject(parameter_object)

    if output_directory:
        elastix_object.SetOutputDirectory(str(output_directory))

    # update filter object
    elastix_object.UpdateLargestPossibleRegion()

    # get results
    result_image = elastix_object.GetOutput()
    result_transform_parameters = elastix_object.GetTransformParameterObject()
    temp_interp_order = result_transform_parameters.GetParameter(
        0, "FinalBSplineInterpolationOrder"
    )
    result_transform_parameters.SetParameter(
        "FinalBSplineInterpolationOrder", "0"
    )

    annotation_image_transformix = itk.transformix_filter(
        annotation_image.astype(np.float32, copy=False),
        result_transform_parameters,
    )

    result_transform_parameters.SetParameter(
        "FinalBSplineInterpolationOrder", temp_interp_order
    )

    transformix_object = itk.TransformixFilter.New(
        moving_image, result_transform_parameters
    )
    transformix_object.SetComputeDeformationField(True)

    if output_directory:
        transformix_object.SetOutputDirectory(str(output_directory))

    transformix_object.UpdateLargestPossibleRegion()

    deformation_field = transformix_object.GetOutputDeformationField()

    if output_directory:
        # Switch the axes from ITK to numpy
        imwrite(
            output_directory / "deformation_field_0.tiff",
            deformation_field[:, :, 1],
        )
        imwrite(
            output_directory / "deformation_field_1.tiff",
            deformation_field[:, :, 0],
        )
        os.unlink(output_directory / "deformationField.tiff")
    else:
        os.unlink("deformationField.tiff")

    return (
        np.asarray(result_image),
        result_transform_parameters,
        np.asarray(annotation_image_transformix),
        deformation_field,
    )


def setup_parameter_object(parameter_lists: List[tuple[str, dict]]):
    """
    Set up the parameter object for the registration process.

    Parameters
    ----------
    parameter_lists : List[tuple[str, dict]], optional
        The list of parameter lists, by default None

    Returns
    -------
    itk.ParameterObject
        The parameter object.#
    """
    parameter_object = itk.ParameterObject.New()

    for transform_type, parameter_dict in parameter_lists:
        parameter_map = parameter_object.GetDefaultParameterMap(transform_type)
        parameter_map.clear()

        for k, v in parameter_dict.items():
            parameter_map[k] = v

        parameter_object.AddParameterMap(parameter_map)

    return parameter_object
