import os
import pandas as pd                                        # data handling
import pandera as pa                                       # data validation
from pandera import Column, DataFrameSchema, Check
from sklearn.pipeline import Pipeline                      # modeling pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from datetime import datetime

# — 1. Load raw data —
RAW_PATH = "ipl_team_stats.csv"
df_raw = pd.read_csv(r"C:\Users\Madv6\ipl_scraper\ipl_team_stats.csv")

# — 2. Define cleaning functions —
def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows."""
    return df.drop_duplicates()

def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing numeric with median, categorical with mode."""
    for col in df.select_dtypes(include="number"):
        df[col] = df[col].fillna(df[col].median())
    for col in df.select_dtypes(include="object"):
        df[col] = df[col].fillna(df[col].mode()[0])
    return df

def enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Convert columns to appropriate types."""
    df["year"] = df["year"].astype(int)
    df["position"] = pd.to_numeric(df["position"], errors="coerce").astype(int)
    return df

# — 3. Validation schema with Pandera —
schema = DataFrameSchema({
    "team":        Column(str,   Check.isin(df_raw["team"].unique()), nullable=False),
    "year":        Column(int,   Check.in_range(2008, datetime.now().year), nullable=False),
    "position":    Column(int,   Check.in_range(1, 10), nullable=False),
    "top_scorer":  Column(str,   Check.str_length(1, 100), nullable=False),
    "top_wickets": Column(str,   Check.str_length(1, 100), nullable=False),
})

def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Run Pandera schema validation (raises on failure)."""
    return schema.validate(df, lazy=True)

# — 4. Feature engineering transformer —
def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features, e.g. ‘experience’ = current year – year."""
    df["experience"] = datetime.now().year - df["year"]
    return df

# — 5. Build sklearn preprocessing pipeline —
numeric_features = ["position", "experience"]
numeric_transformer = Pipeline([
    ("scaler", StandardScaler())
])

categorical_features = ["team"]
categorical_transformer = Pipeline([
    ("onehot", OneHotEncoder(sparse_output=False, handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features),
])

def transform_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return feature matrix X and placeholder y."""
    X = preprocessor.fit_transform(df)
    cat_cols = preprocessor.named_transformers_["cat"]["onehot"].get_feature_names_out(categorical_features)
    return pd.DataFrame(
        X,
        columns=numeric_features + cat_cols.tolist()
    )

# — 6. Full cleaning pipeline via .pipe chaining —
def clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df
        .pipe(drop_duplicates)
        .pipe(fill_missing)
        .pipe(enforce_dtypes)
        .pipe(validate)
        .pipe(add_features)
    )

if __name__ == "__main__":
    # run cleaning
    df_clean = clean_pipeline(df_raw)
    print(f"Cleaned data shape: {df_clean.shape}")

    # transform to model features
    X = transform_features(df_clean)
    print(f"Feature matrix shape: {X.shape}")

    # save cleaned and features
    CLEAN_PATH = "ipl_team_stats_cleaned.csv"
    FEATURES_PATH = "ipl_team_features.csv"
    df_clean.to_csv(CLEAN_PATH, index=False)
    X.to_csv(FEATURES_PATH, index=False)
    print("Saved cleaned and feature data.")

    # — 7. Data versioning with DVC —
    # Run these commands once in your shell to track versions:
    # > dvc init
    # > dvc add ipl_team_stats.csv
    # > dvc add ipl_team_stats_cleaned.csv
    # > dvc add ipl_team_features.csv
    # > git add .dvc config dvc.lock dvc.yaml
    # > git commit -m "Add data versioning for IPL pipeline"
