new_pipeline_conf = {
    "metadata": {"pipeline_name": "iris_pipeline", "iris_version": "1.2.0"},
    "pipeline": [
        {
            "name": "segmentation",
            "algorithm": {"class_name": "iris.MultilabelSegmentation.create_from_hugging_face", "params": {}},
            "inputs": [{"name": "image", "source_node": "input"}],
            "callbacks": None,
        },
        {
            "name": "segmentation_binarization",
            "algorithm": {"class_name": "iris.MultilabelSegmentationBinarization", "params": {
                "eyeball_threshold": 0.2,
                "iris_threshold": 0.2,
                "pupil_threshold": 0.2,
                "eyelashes_threshold": 0.15}},
            "inputs": [{"name": "segmentation_map", "source_node": "segmentation"}],
            "callbacks": None,
        },
        {
            "name": "vectorization",
            "algorithm": {"class_name": "iris.ContouringAlgorithm", "params": {}},
            "inputs": [{"name": "geometry_mask", "source_node": "segmentation_binarization", "index": 0}],
            "callbacks": None,
        },
        {
            "name": "specular_reflection_detection",
            "algorithm": {"class_name": "iris.SpecularReflectionDetection", "params": {
                "reflection_threshold": 200  # Adjusted threshold for specular reflection
            }},
            "inputs": [{"name": "ir_image", "source_node": "input"}],
            "callbacks": None,
        },
        {
            "name": "interpolation",
            "algorithm": {"class_name": "iris.ContourInterpolation", "params": {}},
            "inputs": [{"name": "polygons", "source_node": "vectorization"}],
            "callbacks": None,
        },
        {
            "name": "distance_filter",
            "algorithm": {"class_name": "iris.ContourPointNoiseEyeballDistanceFilter", "params": {}},
            "inputs": [
                {"name": "polygons", "source_node": "interpolation"},
                {"name": "geometry_mask", "source_node": "segmentation_binarization", "index": 1},
            ],
            "callbacks": None,
        },
        {
            "name": "eye_orientation",
            "algorithm": {
                "class_name": "iris.MomentOfArea",
                "params": {
                    "eccentricity_threshold": 0.001  # lowered threshold to allow near-circular eyes
                }
            },
            "inputs": [{"name": "geometries", "source_node": "distance_filter"}],
            "callbacks": None,
        },
        {
            "name": "eye_center_estimation",
            "algorithm": {"class_name": "iris.BisectorsMethod", "params": {}},
            "inputs": [{"name": "geometries", "source_node": "distance_filter"}],
            "callbacks": None,
        },
        {
            "name": "smoothing",
            "algorithm": {"class_name": "iris.Smoothing", "params": {}},
            "inputs": [
                {"name": "polygons", "source_node": "distance_filter"},
                {"name": "eye_centers", "source_node": "eye_center_estimation"},
            ],
            "callbacks": None,
        },
        {
            "name": "geometry_estimation",
            "algorithm": {
                "class_name": "iris.FusionExtrapolation",
                "params": {
                    "circle_extrapolation": {"class_name": "iris.LinearExtrapolation", "params": {"dphi": 0.8}},
                    "ellipse_fit": {"class_name": "iris.LSQEllipseFitWithRefinement", "params": {"dphi": 0.8}},
                    "algorithm_switch_std_threshold": 3.5,
                },
            },
            "inputs": [
                {"name": "input_polygons", "source_node": "distance_filter"},
                {"name": "eye_center", "source_node": "eye_center_estimation"},
            ],
            "callbacks": None,
        },
        {
            "name": "pupil_to_iris_property_estimation",
            "algorithm": {"class_name": "iris.PupilIrisPropertyCalculator", "params": {
                "min_iris_diameter": 50}},
            "inputs": [
                {"name": "geometries", "source_node": "geometry_estimation"},
                {"name": "eye_centers", "source_node": "eye_center_estimation"},
            ],
            "callbacks": None,
        },
        {
            "name": "offgaze_estimation",
            "algorithm": {"class_name": "iris.EccentricityOffgazeEstimation", "params": {}},
            "inputs": [{"name": "geometries", "source_node": "geometry_estimation"}],
            "callbacks": None,
        },
        {
            "name": "occlusion90_calculator",
            "algorithm": {"class_name": "iris.OcclusionCalculator", "params": {"quantile_angle": 45.0}},
            "inputs": [
                {"name": "noise_mask", "source_node": "segmentation_binarization", "index": 1},
                {"name": "extrapolated_polygons", "source_node": "geometry_estimation"},
                {"name": "eye_orientation", "source_node": "eye_orientation"},
                {"name": "eye_centers", "source_node": "eye_center_estimation"},
            ],
            "callbacks": None,
        },
        {
            "name": "occlusion30_calculator",
            "algorithm": {"class_name": "iris.OcclusionCalculator", "params": {"quantile_angle": 30.0}},
            "inputs": [
                {"name": "noise_mask", "source_node": "segmentation_binarization", "index": 1},
                {"name": "extrapolated_polygons", "source_node": "geometry_estimation"},
                {"name": "eye_orientation", "source_node": "eye_orientation"},
                {"name": "eye_centers", "source_node": "eye_center_estimation"},
            ],
            "callbacks": None,
        },
        {
            "name": "noise_masks_aggregation",
            "algorithm": {"class_name": "iris.NoiseMaskUnion", "params": {}},
            "inputs": [
                {
                    "name": "elements",
                    "source_node": [
                        {"name": "segmentation_binarization", "index": 1},
                        {"name": "specular_reflection_detection"},
                    ],
                }
            ],
            "callbacks": None,
        },
        {
            "name": "normalization",
            "algorithm": {"class_name": "iris.PerspectiveNormalization", "params": {}},
            "inputs": [
                {"name": "image", "source_node": "input"},
                {"name": "noise_mask", "source_node": "noise_masks_aggregation"},
                {"name": "extrapolated_contours", "source_node": "geometry_estimation"},
                {"name": "eye_orientation", "source_node": "eye_orientation"},
            ],
            "callbacks": None,
        },
        {
            "name": "sharpness_estimation",
            "algorithm": {"class_name": "iris.SharpnessEstimation", "params": {}},
            "inputs": [{"name": "normalization_output", "source_node": "normalization"}],
            "callbacks": None,
        },
        {
            "name": "filter_bank",
            "algorithm": {
                "class_name": "iris.ConvFilterBank",
                "params": {
                    "filters": [
                        {
                            "class_name": "iris.GaborFilter",
                            "params": {
                                "kernel_size": [41, 21],
                                "sigma_phi": 7,
                                "sigma_rho": 6.13,
                                "theta_degrees": 90.0,
                                "lambda_phi": 28.0,
                                "dc_correction": True,
                                "to_fixpoints": True,
                            },
                        },
                        {
                            "class_name": "iris.GaborFilter",
                            "params": {
                                "kernel_size": [17, 21],
                                "sigma_phi": 2,
                                "sigma_rho": 5.86,
                                "theta_degrees": 90.0,
                                "lambda_phi": 8,
                                "dc_correction": True,
                                "to_fixpoints": True,
                            },
                        },
                    ],
                    "probe_schemas": [
                        {"class_name": "iris.RegularProbeSchema", "params": {"n_rows": 16, "n_cols": 256}},
                        {"class_name": "iris.RegularProbeSchema", "params": {"n_rows": 16, "n_cols": 256}},
                    ],
                },
            },
            "inputs": [{"name": "normalization_output", "source_node": "normalization"}],
            "callbacks": None,
        },
        {
            "name": "encoder",
            "algorithm": {"class_name": "iris.IrisEncoder", "params": {}},
            "inputs": [{"name": "response", "source_node": "filter_bank"}],
            "callbacks": None,
        },
        {
            "name": "bounding_box_estimation",
            "algorithm": {"class_name": "iris.IrisBBoxCalculator", "params": {}},
            "inputs": [
                {"name": "ir_image", "source_node": "input"},
                {"name": "geometry_polygons", "source_node": "geometry_estimation"},
            ],
            "callbacks": None,
        },
    ],
}
