from flask import Flask, render_template, request, jsonify
import os
import numpy as np
from PIL import Image
import logging

try:
    import tensorflow as tf
    tf_available = True
    print('DEBUG: TensorFlow available, version', tf.__version__)
except Exception as ex:
    tf = None
    tf_available = False
    print('DEBUG: TensorFlow not available:', ex)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Path to the Keras .h5 model
MODEL_H5_PATH = os.path.join(os.path.dirname(__file__), 'mobilenet_stable.h5')

# Load Keras model at startup (if available)
model = None
input_shape = None
if tf_available and os.path.exists(MODEL_H5_PATH):
    try:
        # Load Keras model
        model = tf.keras.models.load_model(MODEL_H5_PATH)
        input_shape = model.input_shape  # e.g., (None, H, W, C)
        logging.basicConfig(level=logging.INFO)
        logging.info('Keras model loaded: %s', MODEL_H5_PATH)
        logging.info('Model input shape: %s', input_shape)
        print(f'DEBUG: Loaded Keras model at {MODEL_H5_PATH}. Input shape: {input_shape}')
    except Exception as ex:
        model = None
        logging.basicConfig(level=logging.WARNING)
        logging.warning('Failed to load Keras model: %s', ex)
        print('DEBUG: Exception while loading Keras model:', ex)
else:
    logging.basicConfig(level=logging.WARNING)
    if not tf_available:
        logging.warning('TensorFlow not installed; cannot load .h5 model')
    else:
        logging.warning('Model file not found at %s', MODEL_H5_PATH)
    print('DEBUG: Model file exists:', os.path.exists(MODEL_H5_PATH), 'TensorFlow available:', tf_available)

# Default label mapping for binary classifier. Update if you have a labels file.
LABEL_MAP = {0: 'Benign', 1: 'Malignant'}


def preprocess_image_h5(image_path, model_input_shape):
    # model_input_shape may be like (None, H, W, C) or (H, W, C)
    if isinstance(model_input_shape, (list, tuple)):
        if len(model_input_shape) == 4:
            _, h, w, c = model_input_shape
        elif len(model_input_shape) == 3:
            h, w, c = model_input_shape
        else:
            raise ValueError('Unsupported model input shape: %s' % (model_input_shape,))
    else:
        raise ValueError('Invalid model input shape')

    img = Image.open(image_path).convert('RGB')
    img = img.resize((w, h), Image.BILINEAR)
    arr = np.asarray(img).astype(np.float32) / 255.0
    arr = arr.reshape((1, h, w, c))
    return arr


def postprocess_output_h5(preds, label_map=None):
    # preds expected shape (1, num_classes) or (num_classes,)
    preds_arr = np.asarray(preds)
    if preds_arr.ndim == 2 and preds_arr.shape[0] == 1:
        probs = preds_arr[0]
    else:
        probs = preds_arr

    # Binary sigmoid output (single value)
    if probs.size == 1:
        p = float(probs.flatten()[0])
        p = max(0.0, min(1.0, p))
        pred_idx = 1 if p >= 0.5 else 0
        pred_conf = p if pred_idx == 1 else 1.0 - p
        probs_list = [1.0 - p, p]
        return pred_idx, float(pred_conf), probs_list

    # Multi-class: if outputs look like logits, apply softmax
    if not np.all((probs >= 0) & (probs <= 1)) or abs(np.sum(probs) - 1.0) > 1e-3:
        exp = np.exp(probs - np.max(probs))
        probs = exp / np.sum(exp)

    top_idx = int(np.argmax(probs))
    top_prob = float(np.max(probs))
    return top_idx, top_prob, probs.tolist()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Endpoint for skin scan analysis using a TFLite model.
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if model is None:
        return jsonify({'error': 'Model not loaded. Check server logs.'}), 500

    # Save the uploaded file
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)

    try:
        # Prepare input for Keras model
        logging.info('Received file: %s', file.filename)
        logging.info('Preparing input using model input shape=%s', input_shape)

        x = preprocess_image_h5(filename, input_shape)

        preds = model.predict(x)
        logging.info('Model predict returned shape=%s', np.asarray(preds).shape)

        top_idx, top_prob, all_probs = postprocess_output_h5(preds, label_map=LABEL_MAP)

        logging.info('Inference result top_idx=%s confidence=%s', top_idx, top_prob)

        top_label = LABEL_MAP.get(top_idx, None)

        # For binary models, derive diagnosis using threshold 0.5 on class-1 probability
        diagnosis = None
        confidence_pct = float(top_prob)
        try:
            if isinstance(all_probs, (list, tuple)) and len(all_probs) == 2:
                # all_probs assumed [P(class0), P(class1)]
                p_class1 = float(all_probs[1])
                diagnosis = LABEL_MAP.get(1) if p_class1 >= 0.5 else LABEL_MAP.get(0)
                confidence_pct = p_class1 if p_class1 >= 0.5 else 1.0 - p_class1
            else:
                # multi-class: use top_label
                diagnosis = top_label
        except Exception:
            diagnosis = top_label

        response = {
            'status': 'success',
            'message': 'Image analyzed successfully',
            'analysis': {
                'top_index': top_idx,
                'top_label': top_label,
                'diagnosis': diagnosis,
                'confidence': float(confidence_pct),
                'probabilities': all_probs,
                'raw_prediction': np.asarray(preds).tolist()
            }
        }

        return jsonify(response)
    except Exception as e:
        return jsonify({'error': 'Inference failed', 'details': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'model_loaded': bool(model)}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
