from pathlib import Path
from transformers import Owlv2Processor, Owlv2ForObjectDetection
from PIL import Image
import torch
import numpy as np
from transformers.utils.constants import OPENAI_CLIP_MEAN, OPENAI_CLIP_STD

IMAGE_PATH ='/home/azureuser/20250101_212049.jpg'
OBJECTS_TO_DETECT = ["cat", "dog", "person", "bottle", "cell phone", "remote control", "animal"]
DEFAULT_MODEL_NAME ="google/owlv2-base-patch16-ensemble"
DEFAULT_MODEL_SAVE_PATH ="./owlv2-model"

def get_preprocessed_image(pixel_values):
  pixel_values = pixel_values.squeeze().numpy()
  unnormalized_image = (pixel_values * np.array(OPENAI_CLIP_STD)[:, None, None]) + np.array(OPENAI_CLIP_MEAN)[:, None, None]
  unnormalized_image = (unnormalized_image * 255).astype(np.uint8)
  unnormalized_image = np.moveaxis(unnormalized_image, 0, -1)
  unnormalized_image = Image.fromarray(unnormalized_image)
  return unnormalized_image

def download_and_save_model_and_processor(model_name=DEFAULT_MODEL_NAME, save_directory=DEFAULT_MODEL_SAVE_PATH):
  processor = Owlv2Processor.from_pretrained(model_name)
  model = Owlv2ForObjectDetection.from_pretrained(model_name)
  processor.save_pretrained(save_directory)
  model.save_pretrained(save_directory)

def load_model_and_processor(model_name=DEFAULT_MODEL_NAME, load_directory=None):
  if load_directory is not None:
    processor = Owlv2Processor.from_pretrained(load_directory)
    model = Owlv2ForObjectDetection.from_pretrained(load_directory)
  else:
    processor = Owlv2Processor.from_pretrained(model_name)
    model = Owlv2ForObjectDetection.from_pretrained(model_name)
  return processor, model


def detect_and_count(image_path, 
                     object_texts, 
                     threshold=0.2, 
                     processor=None, 
                     model=None, 
                     model_name=DEFAULT_MODEL_NAME,
                     model_save_path=DEFAULT_MODEL_SAVE_PATH):
  """
  Detect objects specified in `object_texts` in `image_path` and return counts.

  Returns a tuple: (counts_array, detections)
  - counts_array: list of {"type": str, "count": int}
  - detections: list of individual detections with type, score, box
  """
  model_already_downloaded = False
  if processor is None or model is None:
      p = Path(model_save_path)
      if p.exists() and p.is_dir():
          f = Path(model_save_path + "/model.safetensors")
          if f.exists() and f.is_file():
              model_already_downloaded = True
  if(not model_already_downloaded):
      print("Downloading and saving model and processor...")
      download_and_save_model_and_processor(model_name, model_save_path)
  
  processor, model = load_model_and_processor(model_name, model_save_path)
  
  image = Image.open(image_path).convert("RGB")

  # OWL-ViT expects a list of texts per image; first item can be empty (placeholder)
  texts = [[''] + list(object_texts)]
  inputs = processor(text=texts, images=image, return_tensors="pt")

  with torch.no_grad():
    outputs = model(**inputs)

  unnormalized_image = get_preprocessed_image(inputs.pixel_values)
  target_sizes = torch.Tensor([unnormalized_image.size[::-1]])
  results = processor.post_process_grounded_object_detection(outputs=outputs, target_sizes=target_sizes, threshold=threshold)

  boxes = results[0]["boxes"]
  scores = results[0]["scores"]
  labels = results[0]["labels"]

  counts = {t: 0 for t in object_texts}
  detections = []

  for box, score, label in zip(boxes, scores, labels):
    label_text = texts[0][label]
    if label_text in counts and score.item() >= threshold:
      counts[label_text] += 1
      detections.append({
        "type": label_text,
        "score": round(score.item(), 3),
        "box": [round(x, 2) for x in box.tolist()]
      })

  counts_array = [{"type": k, "count": v} for k, v in counts.items()]
  return counts_array, detections


if __name__ == "__main__":
  
  filepath = IMAGE_PATH
  object_texts = OBJECTS_TO_DETECT

  print("Running detection (may download model weights if not cached)...")
  counts, detections = detect_and_count(filepath, object_texts, threshold=0.2)

  print("Counts:")
  for item in counts:
    print(f"- {item['type']}: {item['count']}")

  print("Detections:")
  for d in detections:
    print(f"- {d['type']} (score={d['score']}) box={d['box']}")
