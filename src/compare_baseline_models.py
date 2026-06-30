import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler


base_dir = Path(__file__).resolve().parent.parent
data_path = base_dir / "data" / "dataset.csv"
model_path = base_dir / "models" / "exercise_model.keras"
labels_path = base_dir / "models" / "class_names.json"
results_path = base_dir / "models" / "baseline_comparison_results.csv"


def load_dataset():
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    required_columns = {"label", "split"}
    if not required_columns.issubset(df.columns):
        raise ValueError("Dataset must contain label and split columns")

    ignored_columns = {"label", "split", "source_file", "source_mtime", "feature_version"}
    feature_columns = [column for column in df.columns if column not in ignored_columns]

    encoder = LabelEncoder()
    df["label_encoded"] = encoder.fit_transform(df["label"].values)

    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "validation"]
    test_df = df[df["split"] == "test"]

    if train_df.empty or val_df.empty or test_df.empty:
        raise ValueError("Train, validation and test splits must all contain data")

    return {
        "feature_columns": feature_columns,
        "encoder": encoder,
        "X_train": train_df[feature_columns].values,
        "y_train": train_df["label_encoded"].values,
        "X_val": val_df[feature_columns].values,
        "y_val": val_df["label_encoded"].values,
        "X_test": test_df[feature_columns].values,
        "y_test": test_df["label_encoded"].values,
    }


def summarize_predictions(model_name, y_val, val_pred, y_test, test_pred, class_names):
    val_report = classification_report(
        y_val,
        val_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    test_report = classification_report(
        y_test,
        test_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )

    return {
        "model": model_name,
        "validation_accuracy": accuracy_score(y_val, val_pred),
        "test_accuracy": accuracy_score(y_test, test_pred),
        "test_macro_precision": test_report["macro avg"]["precision"],
        "test_macro_recall": test_report["macro avg"]["recall"],
        "test_macro_f1": test_report["macro avg"]["f1-score"],
        "validation_macro_f1": val_report["macro avg"]["f1-score"],
    }


def evaluate_sklearn_baselines(data):
    models = {
        "Logistic Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=2000, random_state=42)),
        ]),
        "kNN": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", KNeighborsClassifier(n_neighbors=5)),
        ]),
    }

    try:
        from sklearn.ensemble import RandomForestClassifier

        models["Random Forest"] = RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
        )
    except ImportError as error:
        print(f"\nRandom Forest is skipped because it could not be imported: {error}")

    results = []
    for model_name, model in models.items():
        print(f"\nTraining {model_name}...")
        model.fit(data["X_train"], data["y_train"])
        val_pred = model.predict(data["X_val"])
        test_pred = model.predict(data["X_test"])
        results.append(
            summarize_predictions(
                model_name,
                data["y_val"],
                val_pred,
                data["y_test"],
                test_pred,
                data["encoder"].classes_,
            )
        )

    return results


def evaluate_saved_mlp(data):
    if not model_path.exists() or not labels_path.exists():
        print("\nSaved MLP model was not found, skipping MLP evaluation.")
        print("Run src/train_model.py first if you want to include the MLP row.")
        return None

    with open(labels_path, "r", encoding="utf-8") as file:
        model_class_names = json.load(file)

    missing_labels = set(model_class_names) - set(data["encoder"].classes_)
    if missing_labels:
        raise ValueError(f"Saved MLP contains unknown labels: {sorted(missing_labels)}")

    print("\nEvaluating saved Keras MLP...")
    model = tf.keras.models.load_model(model_path)

    val_probs = model.predict(data["X_val"], verbose=0)
    test_probs = model.predict(data["X_test"], verbose=0)

    val_labels = [model_class_names[index] for index in np.argmax(val_probs, axis=1)]
    test_labels = [model_class_names[index] for index in np.argmax(test_probs, axis=1)]

    val_pred = data["encoder"].transform(val_labels)
    test_pred = data["encoder"].transform(test_labels)

    return summarize_predictions(
        "Keras MLP",
        data["y_val"],
        val_pred,
        data["y_test"],
        test_pred,
        data["encoder"].classes_,
    )


def main():
    print("Baseline model comparison")
    data = load_dataset()

    print(f"Feature count: {len(data['feature_columns'])}")
    print(f"Train samples: {len(data['X_train'])}")
    print(f"Validation samples: {len(data['X_val'])}")
    print(f"Test samples: {len(data['X_test'])}")

    results = evaluate_sklearn_baselines(data)
    mlp_result = evaluate_saved_mlp(data)
    if mlp_result:
        results.append(mlp_result)

    results_df = pd.DataFrame(results).sort_values("test_accuracy", ascending=False)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(results_path, index=False)

    print("\nComparison summary:")
    print(results_df.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    main()
