import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
from utils import load_config
from pathlib import Path

CFG = load_config()
LABELED_CSV = CFG.get('labeled_csv', 'samples/labeled_samples.csv')
MODEL_PATH = CFG.get('model_path', 'models/bgthrottle_rf.pkl')
FEATURES = ['cpu_percent','memory_percent','num_threads','proc_age','system_load1']

def run():
    df = pd.read_csv(LABELED_CSV).dropna()
    if 'proc_age' not in df.columns and 'create_time' in df.columns:
        df['proc_age'] = df['ts'] - df['create_time']
    X = df[FEATURES]
    y = df['label_quota']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, max_depth=12, n_jobs=4, random_state=42)
    model.fit(X_train, y_train)
    print('train R2:', model.score(X_train, y_train))
    print('test R2:', model.score(X_test, y_test))
    Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print('saved model ->', MODEL_PATH)

if __name__ == '__main__':
    run()
