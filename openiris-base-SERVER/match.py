'''FOR MATCHING TWO DATASETS


If matching one dataset against self, mode1 and mode2 is the same'''



import cv2
import iris
import os
import numpy as np
from custom_pipeline import new_pipeline_conf
# 1. Create IRISPipeline object
iris_pipeline = iris.IRISPipeline(config=new_pipeline_conf)

dirs="./"
mode1=["dataset1","dataset1","dataset2"]
mode2=["dataset2","dataset1","dataset2"]

folder_to_match="Enhance"

matcher = iris.HammingDistanceMatcher()

for m1, m2 in zip(mode1,mode2):
    # Create a list to store results for this dataset
    results = []

    # Preload all gallery and probe images into arrays
    gallery_images = []
    probe_images = []
    gallery_files = os.listdir(dirs + m1+"/"+folder_to_match+"/" )
    probe_files = os.listdir(dirs + m2+"/"+folder_to_match+"/")

    # Dictionaries to store iris templates for each image
    gallery_templates = {}
    probe_templates = {}

    # Load all gallery images and compute iris templates 
    for gallery in gallery_files:
        try:
            img_gal = cv2.imread(dirs + m1+"/"+folder_to_match+"/" + gallery, cv2.IMREAD_GRAYSCALE)
            output_gal = iris_pipeline(img_gal, eye_side="left")
            gal_code = output_gal['iris_template']
            gallery_templates[gallery] = gal_code  # Store the template
            print("Template gal " + gallery)
        except Exception as e:
            print(f"ERROR: {e}")

    # Load all probe images and compute iris templates 
    for probe in probe_files:
        img_probe = cv2.imread(dirs + m2+ "/"+folder_to_match+"/" + probe, cv2.IMREAD_GRAYSCALE)

        output_probe = iris_pipeline(img_probe, eye_side="left")
        probe_code = output_probe['iris_template']
        probe_templates[probe] = probe_code  # Store the template
        print("Template probe " + probe)

    # Now loop through the gallery and probe templates for matching
    for gallery_name, gal_code in gallery_templates.items():
        for probe_name, probe_code in probe_templates.items():
            try:
                # Compute the Hamming distance between the gallery and probe iris templates
                same_subjects_distance = matcher.run(gal_code, probe_code)

                # Store the result in the list instead of writing to the file immediately
                results.append(f"{gallery_name}, {probe_name}, {same_subjects_distance:.4f}\n")

                print(f"Computed distance between eyes of the {gallery_name} and {probe_name} is {same_subjects_distance:.4f}")

            except Exception as e:
                results.append(f"{gallery_name}, {probe_name}, Error\n")
                print(f"ERROR: {e}")

    # Write all results to the file at once
    with open(m1+"vs"+m2+"_scores.txt", "w") as output_file:
        output_file.write("Gallery Image, Probe Image, Gall Probe Score\n")  # Header line
        output_file.writelines(results)  # Write all results at once
    print(f"Results written to {m1}vs{m2}_scores.txt")