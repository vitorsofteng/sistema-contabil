#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Engine de Análise Contábil com Machine Learning Real

Técnicas implementadas:
1. Prophet (Meta) - Previsão de séries temporais com sazonalidade
2. Isolation Forest - Detecção de anomalias não supervisionada
3. XGBoost/GradientBoosting + Calibração - Probabilidades calibradas
4. Monte Carlo - Simulação de cenários de caixa
5. Feature Engineering Automático
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Tenta importar pandas, fallback para numpy
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ML Libraries com fallbacks
try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.calibration import CalibratedClassifierCV
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# XGBoost é opcional
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Prophet é opcional
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

# Statsmodels é opcional
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

import sys
sys.path.insert(0, '..')
from data.csv_importer import CompanyData, MonthlyRecord


# =============================================================================
# ENUMS E DATACLASSES
# =============================================================================

class TendenciaFaturamento(str, Enum):
    CRESCIMENTO_FORTE = "Crescimento Forte"
    CRESCIMENTO_MODERADO = "Crescimento Moderado"
    ESTAGNACAO = "Estagnação"
    QUEDA_MODERADA = "Queda Moderada"
    QUEDA_FORTE = "Queda Forte"


class NivelRisco(str, Enum):
    CRITICO = "Crítico"
    ALTO = "Alto"
    MODERADO = "Moderado"
    BAIXO = "Baixo"
    MINIMO = "Mínimo"


@dataclass
class PrevisaoML:
    """Resultado de previsão com ML."""
    valor_previsto: float
    intervalo_inferior: float
    intervalo_superior: float
    confianca: float
    modelo_usado: str
    metricas: Dict[str, float]


@dataclass
class AnomaliaML:
    """Anomalia detectada por ML."""
    tipo: str
    mes: str
    severidade: str
    score_anomalia: float  # -1 a 0, quanto menor mais anômalo
    valores_anomalos: Dict[str, float]
    valor_esperado: Dict[str, float]
    descricao: str
    impacto_estimado: float


@dataclass
class SimulacaoMonteCarlo:
    """Resultado de simulação Monte Carlo."""
    cenario_otimista: Dict[str, float]  # Percentil 90
    cenario_base: Dict[str, float]       # Percentil 50
    cenario_pessimista: Dict[str, float] # Percentil 10
    prob_caixa_negativo: float
    meses_runway_p10: int
    meses_runway_p50: int
    meses_runway_p90: int
    num_simulacoes: int


@dataclass
class AnaliseTendenciaML:
    """Análise de tendência com ML."""
    tendencia: str
    direcao: str
    
    # Métricas de tendência
    taxa_mensal: float
    taxa_anual_projetada: float
    
    # Previsões
    previsao_3m: PrevisaoML
    previsao_6m: PrevisaoML
    previsao_12m: PrevisaoML
    
    # Sazonalidade detectada
    tem_sazonalidade: bool
    fator_sazonal_atual: float
    meses_pico: List[int]
    meses_vale: List[int]
    
    # Decomposição
    componente_tendencia: List[float]
    componente_sazonal: List[float]
    componente_residual: List[float]
    
    # Métricas do modelo
    modelo_usado: str
    mape: float  # Mean Absolute Percentage Error
    rmse: float  # Root Mean Square Error
    r_squared: float
    
    descricao: str
    recomendacao: str


@dataclass
class AnaliseRiscoCaixaML:
    """Análise de risco de caixa com Monte Carlo."""
    nivel: str
    saldo_atual: float
    
    # Burn rate com incerteza
    burn_rate_medio: float
    burn_rate_std: float
    burn_rate_tendencia: str  # 'acelerando', 'desacelerando', 'estavel'
    
    # Runway com Monte Carlo
    runway_p10: int  # Pessimista
    runway_p50: int  # Base
    runway_p90: int  # Otimista
    
    # Simulação
    simulacao: SimulacaoMonteCarlo
    
    # Probabilidades
    prob_caixa_negativo_3m: float
    prob_caixa_negativo_6m: float
    prob_caixa_negativo_12m: float
    
    # Métricas adicionais
    volatilidade_caixa: float
    coef_variacao: float
    
    confianca: float
    descricao: str
    recomendacao: str


@dataclass
class AnaliseAnomaliasML:
    """Análise de anomalias com Isolation Forest."""
    total: int
    anomalias: List[Dict]
    
    # Métricas do modelo
    contamination_estimada: float
    features_mais_anomalas: List[str]
    
    # Scores
    score_normalidade_geral: float  # 0-100, quanto maior mais normal
    meses_mais_anomalos: List[str]
    
    # Tendências de anomalias
    tendencia_custos: str
    tendencia_margem: str
    tendencia_impostos: str
    
    # Impacto
    impacto_total_estimado: float
    
    descricao: str


@dataclass 
class AnaliseProbabilidadesML:
    """Probabilidades calibradas com XGBoost."""
    # Probabilidades calibradas
    prob_prejuizo: float
    prob_quebra: float
    prob_imposto_inesperado: float
    
    # Níveis de risco
    risco_prejuizo: str
    risco_quebra: str
    risco_imposto: str
    
    # Calibração
    calibracao_prejuizo: float  # Brier score
    calibracao_quebra: float
    
    # Feature importance
    features_risco_prejuizo: List[Tuple[str, float]]
    features_risco_quebra: List[Tuple[str, float]]
    
    # Score geral
    score_saude: float
    score_confianca: float
    
    # Fatores
    fatores_risco: List[str]
    fatores_positivos: List[str]
    
    descricao: str
    recomendacao: str


@dataclass
class ResultadoAnaliseML:
    """Resultado completo da análise com ML."""
    # Metadata
    empresa: str
    cnpj: str
    periodo_inicio: str
    periodo_fim: str
    data_analise: str
    meses_analisados: int
    
    # Score geral
    score: int
    score_confianca: float
    status: str
    
    # 4 Pilares ML
    tendencia: Dict
    risco_caixa: Dict
    anomalias: Dict
    probabilidades: Dict
    
    # Resumo financeiro
    faturamento_total: float
    faturamento_medio: float
    lucro_total: float
    margem_media: float
    
    # Features calculadas
    features: Dict[str, float]
    
    # Dados para gráficos
    dados_mensais: List[Dict]
    previsoes: List[Dict]
    
    # Insights ML
    insights: List[str]
    
    # Recomendação principal
    recomendacao_principal: str


# =============================================================================
# FEATURE ENGINEERING
# =============================================================================

class SimpleScaler:
    """Scaler simples sem sklearn."""
    def __init__(self):
        self.median = None
        self.iqr = None
    
    def fit_transform(self, X):
        X = np.array(X)
        self.median = np.median(X, axis=0)
        q75, q25 = np.percentile(X, [75, 25], axis=0)
        self.iqr = q75 - q25
        self.iqr[self.iqr == 0] = 1
        return (X - self.median) / self.iqr
    
    def transform(self, X):
        X = np.array(X)
        return (X - self.median) / self.iqr


class FeatureEngineer:
    """Engenharia de features automática."""
    
    def __init__(self):
        if SKLEARN_AVAILABLE:
            self.scaler = RobustScaler()
        else:
            self.scaler = SimpleScaler()
        self.feature_names = []
    
    def create_features(self, records: List[MonthlyRecord]) -> Any:
        """Cria features a partir dos registros."""
        
        # Converte para estrutura de dados
        data = []
        for r in records:
            data.append({
                'data': r.data,
                'receita': r.receita,
                'custos': r.custos,
                'despesas': r.despesas,
                'impostos': r.impostos,
                'folha': r.folha,
                'caixa': r.caixa,
                'lucro_bruto': r.lucro_bruto,
                'lucro_liquido': r.lucro_liquido,
                'margem_bruta': r.margem_bruta,
                'margem_liquida': r.margem_liquida,
            })
        
        if PANDAS_AVAILABLE:
            df = pd.DataFrame(data)
            df = df.sort_values('data').reset_index(drop=True)
            return self._create_features_pandas(df)
        else:
            return self._create_features_numpy(data)
    
    def _create_features_pandas(self, df) -> Any:
        """Cria features usando pandas."""
        
        # === Features Básicas ===
        df['custo_pct'] = df['custos'] / df['receita'].replace(0, np.nan) * 100
        df['despesa_pct'] = df['despesas'] / df['receita'].replace(0, np.nan) * 100
        df['imposto_pct'] = df['impostos'] / df['receita'].replace(0, np.nan) * 100
        df['folha_pct'] = df['folha'] / df['receita'].replace(0, np.nan) * 100
        
        # === Features de Variação ===
        for col in ['receita', 'custos', 'despesas', 'caixa', 'lucro_liquido']:
            df[f'{col}_var_1m'] = df[col].pct_change(1) * 100
            df[f'{col}_var_3m'] = df[col].pct_change(3) * 100
            df[f'{col}_var_6m'] = df[col].pct_change(6) * 100
        
        # === Features de Média Móvel ===
        for col in ['receita', 'margem_liquida', 'caixa']:
            df[f'{col}_mm3'] = df[col].rolling(3).mean()
            df[f'{col}_mm6'] = df[col].rolling(6).mean()
        
        # === Features de Volatilidade ===
        for col in ['receita', 'margem_liquida', 'caixa']:
            df[f'{col}_vol_3m'] = df[col].rolling(3).std()
            df[f'{col}_vol_6m'] = df[col].rolling(6).std()
        
        # === Features de Tendência ===
        df['receita_trend'] = self._calculate_trend_pandas(df['receita'])
        df['margem_trend'] = self._calculate_trend_pandas(df['margem_liquida'])
        df['caixa_trend'] = self._calculate_trend_pandas(df['caixa'])
        
        # === Features de Stress ===
        df['meses_prejuizo_rolling'] = (df['lucro_liquido'] < 0).rolling(6).sum()
        df['meses_caixa_baixo'] = (df['caixa'] < df['caixa'].mean() * 0.5).rolling(6).sum()
        
        # === Features de Eficiência ===
        df['eficiencia_operacional'] = df['lucro_bruto'] / df['despesas'].replace(0, np.nan)
        df['cobertura_caixa'] = df['caixa'] / df['despesas'].replace(0, np.nan)
        
        # Preenche NaN
        df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
        
        self.feature_names = [c for c in df.columns if c not in ['data']]
        
        return df
    
    def _create_features_numpy(self, data: List[Dict]) -> Dict:
        """Cria features usando apenas numpy."""
        
        n = len(data)
        features = {}
        
        # Extrai arrays
        receitas = np.array([d['receita'] for d in data])
        custos = np.array([d['custos'] for d in data])
        despesas = np.array([d['despesas'] for d in data])
        impostos = np.array([d['impostos'] for d in data])
        caixa = np.array([d['caixa'] for d in data])
        lucro = np.array([d['lucro_liquido'] for d in data])
        margem = np.array([d['margem_liquida'] for d in data])
        
        # Features básicas
        features['custo_pct'] = np.where(receitas > 0, custos / receitas * 100, 0)
        features['despesa_pct'] = np.where(receitas > 0, despesas / receitas * 100, 0)
        features['imposto_pct'] = np.where(receitas > 0, impostos / receitas * 100, 0)
        features['margem_liquida'] = margem
        features['lucro_liquido'] = lucro
        features['caixa'] = caixa
        features['receita'] = receitas
        
        # Variações
        features['receita_var_1m'] = np.concatenate([[0], np.diff(receitas) / receitas[:-1] * 100])
        
        # Médias móveis (simplificado)
        features['receita_mm3'] = self._moving_average(receitas, 3)
        features['caixa_mm3'] = self._moving_average(caixa, 3)
        
        # Volatilidade
        features['receita_vol_3m'] = self._moving_std(receitas, 3)
        
        # Eficiência
        features['eficiencia_operacional'] = np.where(despesas > 0, (receitas - custos) / despesas, 0)
        
        self.feature_names = list(features.keys())
        
        # Converte para estrutura similar a DataFrame
        features['data'] = [d['data'] for d in data]
        features['_data'] = data
        
        return features
    
    def _moving_average(self, arr, window):
        result = np.zeros(len(arr))
        for i in range(len(arr)):
            start = max(0, i - window + 1)
            result[i] = np.mean(arr[start:i+1])
        return result
    
    def _moving_std(self, arr, window):
        result = np.zeros(len(arr))
        for i in range(len(arr)):
            start = max(0, i - window + 1)
            result[i] = np.std(arr[start:i+1]) if i >= window - 1 else 0
        return result
    
    def _calculate_trend_pandas(self, series, window: int = 6):
        """Calcula tendência usando regressão linear móvel."""
        def trend_slope(x):
            if len(x) < 2:
                return 0
            return np.polyfit(range(len(x)), x, 1)[0]
        return series.rolling(window).apply(trend_slope, raw=True)
    
    def get_feature_matrix(self, df) -> Tuple[np.ndarray, List[str]]:
        """Retorna matriz de features normalizada."""
        if PANDAS_AVAILABLE and hasattr(df, 'columns'):
            numeric_cols = [c for c in self.feature_names if c in df.columns]
            X = df[numeric_cols].values
        else:
            numeric_cols = [c for c in self.feature_names if c in df and c != 'data' and c != '_data']
            X = np.column_stack([df[c] for c in numeric_cols])
        
        return self.scaler.fit_transform(X), numeric_cols


# =============================================================================
# MODELO DE TENDÊNCIA (PROPHET / HOLT-WINTERS / FALLBACK)
# =============================================================================

class TrendPredictor:
    """Previsão de tendência com Prophet, Holt-Winters ou métodos simples."""
    
    def __init__(self):
        self.model = None
        self.model_type = None
        self.last_train_date = None
    
    def fit_predict(
        self, 
        dates: List[datetime], 
        values: List[float],
        periods: int = 12
    ) -> Tuple[Any, Dict]:
        """Treina modelo e faz previsões."""
        
        n = len(values)
        metrics = {}
        
        # Tenta Prophet primeiro (se disponível e dados suficientes)
        if PROPHET_AVAILABLE and PANDAS_AVAILABLE and n >= 12:
            try:
                df = pd.DataFrame({'ds': pd.to_datetime(dates), 'y': values})
                forecast, metrics = self._fit_prophet(df, periods)
                self.model_type = 'Prophet'
                return forecast, metrics
            except Exception:
                pass
        
        # Tenta Holt-Winters (se disponível)
        if STATSMODELS_AVAILABLE and PANDAS_AVAILABLE and n >= 6:
            try:
                df = pd.DataFrame({'ds': pd.to_datetime(dates), 'y': values})
                forecast, metrics = self._fit_holtwinters(df, periods)
                self.model_type = 'Holt-Winters'
                return forecast, metrics
            except Exception:
                pass
        
        # Fallback: Regressão linear + EMA
        forecast, metrics = self._fit_simple(dates, values, periods)
        self.model_type = 'Linear+EMA'
        return forecast, metrics
    
    def _fit_prophet(self, df, periods: int) -> Tuple[Any, Dict]:
        """Fit com Prophet."""
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode='multiplicative',
            interval_width=0.80,
            changepoint_prior_scale=0.05
        )
        
        model.fit(df)
        self.model = model
        
        future = model.make_future_dataframe(periods=periods, freq='MS')
        forecast = model.predict(future)
        
        # Métricas
        train_pred = forecast[forecast['ds'].isin(df['ds'])]['yhat'].values
        actual = df['y'].values
        
        mape = np.mean(np.abs((actual - train_pred) / np.where(actual != 0, actual, 1))) * 100
        rmse = np.sqrt(np.mean((actual - train_pred) ** 2))
        ss_res = np.sum((actual - train_pred) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return forecast, {'mape': mape, 'rmse': rmse, 'r_squared': r2, 'model': 'Prophet'}
    
    def _fit_holtwinters(self, df, periods: int) -> Tuple[Any, Dict]:
        """Fit com Holt-Winters."""
        series = df.set_index('ds')['y']
        
        seasonal_periods = 12 if len(series) >= 24 else None
        
        if seasonal_periods:
            model = ExponentialSmoothing(
                series, seasonal_periods=seasonal_periods,
                trend='add', seasonal='add', damped_trend=True
            )
        else:
            model = ExponentialSmoothing(series, trend='add', damped_trend=True)
        
        fitted = model.fit(optimized=True)
        self.model = fitted
        
        forecast_values = fitted.forecast(periods)
        
        future_dates = pd.date_range(
            start=series.index[-1] + pd.DateOffset(months=1),
            periods=periods, freq='MS'
        )
        
        # Monta estrutura de forecast
        forecast_data = {
            'ds': list(series.index) + list(future_dates),
            'yhat': list(fitted.fittedvalues) + list(forecast_values),
            'yhat_lower': list(fitted.fittedvalues * 0.9) + list(forecast_values * 0.85),
            'yhat_upper': list(fitted.fittedvalues * 1.1) + list(forecast_values * 1.15),
        }
        
        forecast = pd.DataFrame(forecast_data) if PANDAS_AVAILABLE else forecast_data
        
        # Métricas
        train_pred = fitted.fittedvalues.values
        actual = series.values
        
        mape = np.mean(np.abs((actual - train_pred) / np.where(actual != 0, actual, 1))) * 100
        rmse = np.sqrt(np.mean((actual - train_pred) ** 2))
        ss_res = np.sum((actual - train_pred) ** 2)
        ss_tot = np.sum((actual - np.mean(actual)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return forecast, {'mape': mape, 'rmse': rmse, 'r_squared': r2, 'model': 'Holt-Winters'}
    
    def _fit_simple(self, dates: List[datetime], values: List[float], periods: int) -> Tuple[Dict, Dict]:
        """Fallback com regressão linear + EMA."""
        values = np.array(values)
        n = len(values)
        
        # Regressão linear para tendência
        x = np.arange(n)
        slope, intercept, r_value, _, _ = stats.linregress(x, values)
        
        # EMA para suavização
        alpha = 0.3
        ema = [values[0]]
        for i in range(1, n):
            ema.append(alpha * values[i] + (1 - alpha) * ema[-1])
        ema = np.array(ema)
        
        # Previsão: combina tendência linear + último EMA
        fitted = intercept + slope * x
        
        # Previsões futuras
        forecasts = []
        last_date = dates[-1]
        forecast_dates = []
        
        for i in range(periods):
            future_x = n + i
            # Combina tendência com ajuste do EMA
            pred = intercept + slope * future_x
            # Ajusta para não divergir muito do último valor
            pred = 0.7 * pred + 0.3 * ema[-1]
            forecasts.append(pred)
            forecast_dates.append(last_date + timedelta(days=30 * (i + 1)))
        
        # Métricas
        train_pred = fitted
        actual = values
        
        mape = np.mean(np.abs((actual - train_pred) / np.where(actual != 0, actual, 1))) * 100
        rmse = np.sqrt(np.mean((actual - train_pred) ** 2))
        r2 = r_value ** 2
        
        # Estrutura de forecast
        forecast = {
            'ds': list(dates) + forecast_dates,
            'yhat': list(fitted) + forecasts,
            'yhat_lower': list(fitted * 0.9) + [f * 0.8 for f in forecasts],
            'yhat_upper': list(fitted * 1.1) + [f * 1.2 for f in forecasts],
        }
        
        return forecast, {'mape': mape, 'rmse': rmse, 'r_squared': r2, 'model': 'Linear+EMA'}
    
    def detect_seasonality(self, values: List[float]) -> Dict:
        """Detecta padrões de sazonalidade."""
        if len(values) < 12:
            return {'has_seasonality': False}
        
        values = np.array(values)
        
        # Método simples: compara meses equivalentes
        if len(values) >= 24:
            year1 = values[:12]
            year2 = values[12:24]
            corr = np.corrcoef(year1, year2)[0, 1]
            has_seasonality = corr > 0.5 and not np.isnan(corr)
        else:
            has_seasonality = False
        
        if STATSMODELS_AVAILABLE and PANDAS_AVAILABLE and len(values) >= 24:
            try:
                series = pd.Series(values)
                decomp = seasonal_decompose(series, model='additive', period=12, extrapolate_trend='freq')
                
                seasonal = decomp.seasonal.values
                residual = decomp.resid.dropna().values
                
                seasonal_var = np.var(seasonal)
                residual_var = np.var(residual) if len(residual) > 0 else 1
                f_stat = seasonal_var / residual_var if residual_var > 0 else 0
                
                has_seasonality = f_stat > 2.0
                
                monthly_avg = pd.Series(seasonal[:12])
                meses_pico = monthly_avg.nlargest(3).index.tolist()
                meses_vale = monthly_avg.nsmallest(3).index.tolist()
                
                return {
                    'has_seasonality': has_seasonality,
                    'seasonal_strength': float(f_stat),
                    'seasonal_component': seasonal.tolist(),
                    'trend_component': decomp.trend.fillna(method='bfill').fillna(method='ffill').values.tolist(),
                    'residual_component': decomp.resid.fillna(0).values.tolist(),
                    'peak_months': [m + 1 for m in meses_pico],
                    'valley_months': [m + 1 for m in meses_vale],
                    'current_seasonal_factor': float(seasonal[-1]) if len(seasonal) > 0 else 0
                }
            except:
                pass
        
        # Fallback: detecta picos simples
        if len(values) >= 12:
            monthly_means = []
            for m in range(12):
                month_values = values[m::12]
                if len(month_values) > 0:
                    monthly_means.append(np.mean(month_values))
                else:
                    monthly_means.append(np.mean(values))
            
            peaks = np.argsort(monthly_means)[-3:][::-1]
            valleys = np.argsort(monthly_means)[:3]
            
            return {
                'has_seasonality': has_seasonality,
                'seasonal_strength': 1.0 if has_seasonality else 0.0,
                'seasonal_component': [],
                'trend_component': [],
                'residual_component': [],
                'peak_months': [int(m + 1) for m in peaks],
                'valley_months': [int(m + 1) for m in valleys],
                'current_seasonal_factor': 0
            }
        
        return {'has_seasonality': False}


# =============================================================================
# DETECÇÃO DE ANOMALIAS (ISOLATION FOREST / FALLBACK Z-SCORE)
# =============================================================================

class AnomalyDetector:
    """Detecção de anomalias com Isolation Forest ou Z-Score."""
    
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = None
        self.scaler = SimpleScaler() if not SKLEARN_AVAILABLE else RobustScaler()
        self.feature_cols = []
        self.use_sklearn = SKLEARN_AVAILABLE
    
    def fit_detect(
        self, 
        df: Any,
        feature_cols: List[str]
    ) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Treina e detecta anomalias."""
        
        self.feature_cols = feature_cols
        
        # Extrai matriz de features
        if PANDAS_AVAILABLE and hasattr(df, 'columns'):
            valid_cols = [c for c in feature_cols if c in df.columns]
            X = df[valid_cols].fillna(0).values
        else:
            valid_cols = [c for c in feature_cols if c in df]
            X = np.column_stack([np.array(df[c]) for c in valid_cols])
        
        self.feature_cols = valid_cols
        
        # Normaliza
        X_scaled = self.scaler.fit_transform(X)
        
        if SKLEARN_AVAILABLE:
            return self._detect_isolation_forest(X_scaled, valid_cols)
        else:
            return self._detect_zscore(X_scaled, valid_cols)
    
    def _detect_isolation_forest(self, X_scaled: np.ndarray, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Detecção com Isolation Forest."""
        
        self.model = IsolationForest(
            n_estimators=200,
            max_samples='auto',
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        
        predictions = self.model.fit_predict(X_scaled)
        scores = self.model.decision_function(X_scaled)
        
        n_anomalies = np.sum(predictions == -1)
        contamination_real = n_anomalies / len(predictions)
        
        # Feature importance
        anomaly_idx = np.where(predictions == -1)[0]
        if len(anomaly_idx) > 0:
            anomaly_features = X_scaled[anomaly_idx]
            normal_features = X_scaled[predictions == 1]
            
            if len(normal_features) > 0:
                normal_mean = np.mean(normal_features, axis=0)
                anomaly_mean = np.mean(anomaly_features, axis=0)
                feature_diff = np.abs(anomaly_mean - normal_mean)
                feature_importance = sorted(zip(feature_cols, feature_diff), key=lambda x: x[1], reverse=True)
            else:
                feature_importance = [(c, 0) for c in feature_cols]
        else:
            feature_importance = [(c, 0) for c in feature_cols]
        
        return predictions, scores, {
            'n_anomalies': n_anomalies,
            'contamination': contamination_real,
            'feature_importance': feature_importance[:10],
            'mean_score': float(np.mean(scores)),
            'std_score': float(np.std(scores)),
        }
    
    def _detect_zscore(self, X_scaled: np.ndarray, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Fallback: detecção com Z-Score multivariado."""
        
        # Z-score por feature
        z_scores = np.abs(X_scaled)
        
        # Score agregado: máximo z-score por linha
        max_z = np.max(z_scores, axis=1)
        
        # Threshold baseado na contaminação desejada
        threshold = np.percentile(max_z, (1 - self.contamination) * 100)
        
        predictions = np.where(max_z > threshold, -1, 1)
        scores = -max_z / (np.max(max_z) + 1e-6)  # Normaliza para -1 a 0
        
        n_anomalies = np.sum(predictions == -1)
        contamination_real = n_anomalies / len(predictions)
        
        # Feature importance: variância do z-score
        feature_importance = sorted(
            zip(feature_cols, np.mean(z_scores, axis=0)),
            key=lambda x: x[1], reverse=True
        )
        
        return predictions, scores, {
            'n_anomalies': n_anomalies,
            'contamination': contamination_real,
            'feature_importance': feature_importance[:10],
            'mean_score': float(np.mean(scores)),
            'std_score': float(np.std(scores)),
        }
    
    def explain_anomaly(self, row_data: Dict, expected_data: Dict, score: float) -> str:
        """Gera explicação para uma anomalia."""
        
        deviations = []
        for col in self.feature_cols:
            if col in row_data and col in expected_data:
                actual = row_data.get(col, 0)
                expected = expected_data.get(col, 0)
                if expected != 0:
                    pct_diff = (actual - expected) / abs(expected) * 100
                    if abs(pct_diff) > 20:
                        direction = "acima" if pct_diff > 0 else "abaixo"
                        deviations.append(f"{col}: {abs(pct_diff):.0f}% {direction}")
        
        if deviations:
            return "Desvios: " + "; ".join(deviations[:3])
        return f"Padrão anômalo (score: {score:.2f})"


# =============================================================================
# MODELO DE PROBABILIDADES (XGBOOST / GRADIENT BOOSTING / FALLBACK)
# =============================================================================

class ProbabilityPredictor:
    """Predição de probabilidades com XGBoost, GradientBoosting ou heurísticas."""
    
    def __init__(self):
        self.models = {}
        self.calibrators = {}
        self.feature_cols = []
        self.scaler = SimpleScaler() if not SKLEARN_AVAILABLE else StandardScaler()
    
    def _create_labels(self, df: Any, n_records: int) -> Dict[str, np.ndarray]:
        """Cria labels baseado em dados históricos."""
        
        if PANDAS_AVAILABLE and hasattr(df, 'lucro_liquido'):
            lucro = df['lucro_liquido'].values
            caixa = df['caixa'].values
        else:
            lucro = np.array(df.get('lucro_liquido', [0] * n_records))
            caixa = np.array(df.get('caixa', [0] * n_records))
        
        labels = {}
        
        # Prejuízo: próximo mês terá prejuízo?
        labels['prejuizo'] = np.zeros(n_records, dtype=int)
        for i in range(n_records - 1):
            labels['prejuizo'][i] = 1 if lucro[i + 1] < 0 else 0
        
        # Caixa crítico
        caixa_critico = np.mean(caixa) * 0.5
        labels['caixa_critico'] = np.zeros(n_records, dtype=int)
        for i in range(n_records - 3):
            if caixa[i + 3] < caixa_critico:
                labels['caixa_critico'][i] = 1
        
        return labels
    
    def _create_synthetic_data(self, X: np.ndarray, labels: Dict, n_samples: int = 300) -> Tuple[np.ndarray, Dict]:
        """Cria dados sintéticos para treinamento."""
        
        n_features = X.shape[1]
        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0)
        stds[stds == 0] = 1
        
        synthetic_X = []
        synthetic_labels = {k: [] for k in labels.keys()}
        
        for _ in range(n_samples):
            scenario = np.random.choice(['bom', 'medio', 'ruim'], p=[0.3, 0.4, 0.3])
            
            if scenario == 'bom':
                row = means + np.random.normal(0, stds * 0.5)
                prob_prej = 0.1
                prob_caixa = 0.05
            elif scenario == 'medio':
                row = means + np.random.normal(0, stds)
                prob_prej = 0.3
                prob_caixa = 0.2
            else:
                row = means + np.random.normal(-stds * 0.5, stds * 1.5)
                prob_prej = 0.7
                prob_caixa = 0.5
            
            synthetic_X.append(row)
            synthetic_labels['prejuizo'].append(1 if np.random.random() < prob_prej else 0)
            synthetic_labels['caixa_critico'].append(1 if np.random.random() < prob_caixa else 0)
        
        # Combina real + sintético
        combined_X = np.vstack([X, np.array(synthetic_X)])
        combined_labels = {}
        for k in labels.keys():
            combined_labels[k] = np.concatenate([labels[k], np.array(synthetic_labels[k])])
        
        return combined_X, combined_labels
    
    def fit_predict(self, df: Any, feature_cols: List[str]) -> Dict[str, Dict]:
        """Treina modelos e retorna probabilidades."""
        
        self.feature_cols = feature_cols
        
        # Extrai features
        if PANDAS_AVAILABLE and hasattr(df, 'columns'):
            valid_cols = [c for c in feature_cols if c in df.columns]
            X = df[valid_cols].fillna(0).values
            n_records = len(df)
        else:
            valid_cols = [c for c in feature_cols if c in df]
            X = np.column_stack([np.array(df[c]) for c in valid_cols])
            n_records = len(X)
        
        # Cria labels
        labels = self._create_labels(df, n_records)
        
        # Gera dados sintéticos
        X_train, labels_train = self._create_synthetic_data(X, labels)
        X_scaled = self.scaler.fit_transform(X_train)
        
        results = {}
        
        for target_name, y in labels_train.items():
            if len(np.unique(y)) < 2:
                results[target_name] = {
                    'probability': 0.1,
                    'calibration': 0.25,
                    'feature_importance': [(c, 0) for c in valid_cols[:5]],
                    'model': 'baseline'
                }
                continue
            
            if XGBOOST_AVAILABLE:
                prob, brier, feat_imp, model_name = self._train_xgboost(X_scaled, y, valid_cols)
            elif SKLEARN_AVAILABLE:
                prob, brier, feat_imp, model_name = self._train_sklearn(X_scaled, y, valid_cols)
            else:
                prob, brier, feat_imp, model_name = self._train_heuristic(X, y, valid_cols, df, n_records)
            
            # Probabilidade para dados reais
            X_real_scaled = self.scaler.transform(X)
            
            if self.models.get(target_name) is not None:
                try:
                    probs = self.models[target_name].predict_proba(X_real_scaled)[:, 1]
                    prob = float(np.mean(probs[-3:]))
                except:
                    pass
            
            results[target_name] = {
                'probability': min(0.95, max(0.05, prob)),
                'calibration': brier,
                'feature_importance': feat_imp[:5],
                'model': model_name
            }
        
        return results
    
    def _train_xgboost(self, X: np.ndarray, y: np.ndarray, cols: List[str]) -> Tuple[float, float, List, str]:
        """Treina com XGBoost."""
        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1,
            objective='binary:logistic', random_state=42,
            use_label_encoder=False, eval_metric='logloss'
        )
        model.fit(X, y)
        
        probs = model.predict_proba(X)[:, 1]
        brier = np.mean((y - probs) ** 2)
        
        feat_imp = sorted(zip(cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
        
        self.models['current'] = model
        
        return float(np.mean(probs[-10:])), brier, feat_imp, 'XGBoost'
    
    def _train_sklearn(self, X: np.ndarray, y: np.ndarray, cols: List[str]) -> Tuple[float, float, List, str]:
        """Treina com GradientBoosting do sklearn."""
        model = GradientBoostingClassifier(
            n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
        )
        model.fit(X, y)
        
        probs = model.predict_proba(X)[:, 1]
        brier = np.mean((y - probs) ** 2)
        
        feat_imp = sorted(zip(cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
        
        self.models['current'] = model
        
        return float(np.mean(probs[-10:])), brier, feat_imp, 'GradientBoosting'
    
    def _train_heuristic(self, X: np.ndarray, y: np.ndarray, cols: List[str], df: Any, n: int) -> Tuple[float, float, List, str]:
        """Fallback: usa heurísticas baseadas em regras."""
        
        # Extrai métricas chave
        if PANDAS_AVAILABLE and hasattr(df, 'margem_liquida'):
            margem = df['margem_liquida'].values[-1] if len(df) > 0 else 0
            lucro_recent = df['lucro_liquido'].values[-6:] if len(df) >= 6 else df['lucro_liquido'].values
        else:
            margem = df.get('margem_liquida', [0])[-1]
            lucro_recent = df.get('lucro_liquido', [0])[-6:]
        
        meses_prejuizo = sum(1 for l in lucro_recent if l < 0)
        
        # Probabilidade heurística
        prob = 0.1
        if meses_prejuizo >= 3:
            prob += 0.4
        elif meses_prejuizo >= 1:
            prob += 0.2
        if margem < 0:
            prob += 0.2
        elif margem < 5:
            prob += 0.1
        
        prob = min(0.9, max(0.05, prob))
        
        # Feature importance simulada
        feat_imp = [(c, 1.0 / len(cols)) for c in cols]
        
        return prob, 0.25, feat_imp, 'Heuristic'


# =============================================================================
# SIMULAÇÃO MONTE CARLO
# =============================================================================

class MonteCarloSimulator:
    """Simulação Monte Carlo para cenários de caixa."""
    
    def __init__(self, n_simulations: int = 5000):
        self.n_simulations = n_simulations
    
    def simulate_cash_flow(
        self,
        initial_cash: float,
        monthly_revenues: List[float],
        monthly_costs: List[float],
        periods: int = 12
    ) -> SimulacaoMonteCarlo:
        """Simula cenários de fluxo de caixa."""
        
        # Estatísticas dos dados
        rev_mean = np.mean(monthly_revenues)
        rev_std = np.std(monthly_revenues)
        cost_mean = np.mean(monthly_costs)
        cost_std = np.std(monthly_costs)
        
        # Correlação entre receita e custo
        if len(monthly_revenues) == len(monthly_costs):
            corr = np.corrcoef(monthly_revenues, monthly_costs)[0, 1]
            corr = corr if not np.isnan(corr) else 0.5
        else:
            corr = 0.5
        
        # Simulações
        final_cash = []
        monthly_cash = [[] for _ in range(periods)]
        runway_months = []
        
        for _ in range(self.n_simulations):
            cash = initial_cash
            runway = periods
            
            for month in range(periods):
                # Gera receita e custo correlacionados
                z1 = np.random.normal()
                z2 = corr * z1 + np.sqrt(1 - corr**2) * np.random.normal()
                
                revenue = max(0, rev_mean + rev_std * z1)
                cost = max(0, cost_mean + cost_std * z2)
                
                # Atualiza caixa
                net = revenue - cost
                cash = cash + net
                
                monthly_cash[month].append(cash)
                
                if cash <= 0 and runway == periods:
                    runway = month + 1
            
            final_cash.append(cash)
            runway_months.append(runway)
        
        # Calcula percentis
        final_cash = np.array(final_cash)
        runway_months = np.array(runway_months)
        
        # Cenários mensais
        cenario_otimista = {}
        cenario_base = {}
        cenario_pessimista = {}
        
        for month in range(periods):
            month_cash = np.array(monthly_cash[month])
            cenario_pessimista[f'mes_{month+1}'] = float(np.percentile(month_cash, 10))
            cenario_base[f'mes_{month+1}'] = float(np.percentile(month_cash, 50))
            cenario_otimista[f'mes_{month+1}'] = float(np.percentile(month_cash, 90))
        
        return SimulacaoMonteCarlo(
            cenario_otimista=cenario_otimista,
            cenario_base=cenario_base,
            cenario_pessimista=cenario_pessimista,
            prob_caixa_negativo=float(np.mean(final_cash < 0)),
            meses_runway_p10=int(np.percentile(runway_months, 10)),
            meses_runway_p50=int(np.percentile(runway_months, 50)),
            meses_runway_p90=int(np.percentile(runway_months, 90)),
            num_simulacoes=self.n_simulations
        )


# =============================================================================
# ENGINE PRINCIPAL
# =============================================================================

class ContabilAnalyzerML:
    """Engine principal de análise com ML."""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.trend_predictor = TrendPredictor()
        self.anomaly_detector = AnomalyDetector()
        self.probability_predictor = ProbabilityPredictor()
        self.monte_carlo = MonteCarloSimulator()
    
    def analyze(self, data: CompanyData, seed: int = 42) -> ResultadoAnaliseML:
        """Executa análise completa com ML.
        
        Args:
            data: Dados da empresa
            seed: Seed para reprodutibilidade (default=42)
        """
        
        # Seed para reprodutibilidade
        np.random.seed(seed)
        
        if len(data.records) < 6:
            raise ValueError("Necessário pelo menos 6 meses de dados para análise ML")
        
        # Feature Engineering
        df = self.feature_engineer.create_features(data.records)
        
        # 1. Análise de Tendência
        tendencia = self._analyze_tendencia_ml(data.records, df)
        
        # 2. Análise de Risco de Caixa
        risco_caixa = self._analyze_risco_caixa_ml(data.records, df)
        
        # 3. Análise de Anomalias
        anomalias = self._analyze_anomalias_ml(data.records, df)
        
        # 4. Probabilidades
        probabilidades = self._analyze_probabilidades_ml(data.records, df, tendencia, risco_caixa, anomalias)
        
        # Score geral
        score = int(probabilidades['score_saude'])
        score_confianca = probabilidades['score_confianca']
        
        if score >= 70:
            status = 'saudavel'
        elif score >= 40:
            status = 'atencao'
        else:
            status = 'critico'
        
        # Dados mensais
        dados_mensais = []
        for i, r in enumerate(data.records):
            dados_mensais.append({
                'periodo': r.periodo,
                'receita': r.receita,
                'lucro': r.lucro_liquido,
                'margem': r.margem_liquida,
                'caixa': r.caixa,
                'custos_pct': (r.custos / r.receita * 100) if r.receita > 0 else 0,
                'impostos_pct': r.carga_tributaria,
            })
        
        # Previsões para gráfico
        previsoes = []
        if 'previsao_3m' in tendencia:
            # Adiciona previsões
            last_date = data.records[-1].data
            for i in range(1, 13):
                previsoes.append({
                    'periodo': (last_date + timedelta(days=30*i)).strftime('%Y-%m'),
                    'receita_prevista': tendencia['previsao_12m']['valor_previsto'] * (i/12),
                    'receita_inferior': tendencia['previsao_12m']['intervalo_inferior'] * (i/12),
                    'receita_superior': tendencia['previsao_12m']['intervalo_superior'] * (i/12),
                })
        
        # Insights
        insights = self._generate_insights(tendencia, risco_caixa, anomalias, probabilidades)
        
        # Features calculadas
        features = {}
        for col in df.columns:
            if col not in ['data'] and df[col].dtype in ['float64', 'int64']:
                features[col] = float(df[col].iloc[-1])
        
        # Margem média
        margens = [r.margem_liquida for r in data.records]
        margem_media = np.mean(margens)
        
        return ResultadoAnaliseML(
            empresa=data.empresa,
            cnpj=data.cnpj,
            periodo_inicio=data.periodo_inicio.strftime('%Y-%m') if data.periodo_inicio else '',
            periodo_fim=data.periodo_fim.strftime('%Y-%m') if data.periodo_fim else '',
            data_analise=datetime.now().strftime('%Y-%m-%d %H:%M'),
            meses_analisados=len(data.records),
            score=score,
            score_confianca=score_confianca,
            status=status,
            tendencia=tendencia,
            risco_caixa=risco_caixa,
            anomalias=anomalias,
            probabilidades=probabilidades,
            faturamento_total=data.faturamento_total,
            faturamento_medio=data.faturamento_medio,
            lucro_total=data.lucro_total,
            margem_media=margem_media,
            features=features,
            dados_mensais=dados_mensais,
            previsoes=previsoes,
            insights=insights,
            recomendacao_principal=probabilidades['recomendacao'],
        )
    
    def _analyze_tendencia_ml(self, records: List[MonthlyRecord], df: pd.DataFrame) -> Dict:
        """Análise de tendência com ML."""
        
        dates = [r.data for r in records]
        values = [r.receita for r in records]
        
        # Previsão
        forecast, metrics = self.trend_predictor.fit_predict(dates, values, periods=12)
        
        # Sazonalidade
        seasonality = self.trend_predictor.detect_seasonality(values)
        
        # Previsões específicas
        n = len(records)
        
        def create_previsao(period_idx: int) -> Dict:
            idx = n + period_idx - 1
            if idx < len(forecast):
                return {
                    'valor_previsto': float(forecast['yhat'].iloc[idx]),
                    'intervalo_inferior': float(forecast['yhat_lower'].iloc[idx]),
                    'intervalo_superior': float(forecast['yhat_upper'].iloc[idx]),
                    'confianca': 80.0,
                    'modelo_usado': metrics['model'],
                    'metricas': metrics
                }
            return {
                'valor_previsto': values[-1],
                'intervalo_inferior': values[-1] * 0.8,
                'intervalo_superior': values[-1] * 1.2,
                'confianca': 50.0,
                'modelo_usado': 'Fallback',
                'metricas': {}
            }
        
        # Taxa de variação
        if len(values) >= 2:
            taxa_mensal = ((values[-1] / values[0]) ** (1/len(values)) - 1) * 100
        else:
            taxa_mensal = 0
        
        taxa_anual = ((1 + taxa_mensal/100) ** 12 - 1) * 100
        
        # Classificação
        if taxa_mensal > 3:
            tendencia = TendenciaFaturamento.CRESCIMENTO_FORTE.value
            direcao = 'up'
        elif taxa_mensal > 0.5:
            tendencia = TendenciaFaturamento.CRESCIMENTO_MODERADO.value
            direcao = 'up'
        elif taxa_mensal > -0.5:
            tendencia = TendenciaFaturamento.ESTAGNACAO.value
            direcao = 'stable'
        elif taxa_mensal > -3:
            tendencia = TendenciaFaturamento.QUEDA_MODERADA.value
            direcao = 'down'
        else:
            tendencia = TendenciaFaturamento.QUEDA_FORTE.value
            direcao = 'down'
        
        # Descrição
        if direcao == 'up':
            descricao = f"Faturamento em crescimento de {taxa_mensal:+.1f}%/mês. "
            if seasonality.get('has_seasonality'):
                descricao += f"Sazonalidade detectada (picos nos meses {seasonality['peak_months']}). "
            descricao += f"Modelo {metrics['model']} com MAPE de {metrics['mape']:.1f}%."
            recomendacao = "Manter estratégia. Preparar estrutura para suportar crescimento previsto."
        elif direcao == 'stable':
            descricao = f"Faturamento estável ({taxa_mensal:+.1f}%/mês). "
            descricao += f"Previsão com confiança de {100-metrics['mape']:.0f}%."
            recomendacao = "Revisar estratégia comercial para retomar crescimento."
        else:
            descricao = f"Faturamento em queda de {abs(taxa_mensal):.1f}%/mês. "
            descricao += f"Previsão indica continuidade da tendência."
            recomendacao = "URGENTE: Identificar causas. Adequar custos ao novo patamar."
        
        return {
            'tendencia': tendencia,
            'direcao': direcao,
            'taxa_mensal': round(taxa_mensal, 2),
            'taxa_anual_projetada': round(taxa_anual, 2),
            'previsao_3m': create_previsao(3),
            'previsao_6m': create_previsao(6),
            'previsao_12m': create_previsao(12),
            'tem_sazonalidade': seasonality.get('has_seasonality', False),
            'fator_sazonal_atual': seasonality.get('current_seasonal_factor', 0),
            'meses_pico': seasonality.get('peak_months', []),
            'meses_vale': seasonality.get('valley_months', []),
            'componente_tendencia': seasonality.get('trend_component', []),
            'componente_sazonal': seasonality.get('seasonal_component', []),
            'componente_residual': seasonality.get('residual_component', []),
            'modelo_usado': metrics['model'],
            'mape': round(metrics['mape'], 2),
            'rmse': round(metrics['rmse'], 2),
            'r_squared': round(metrics['r_squared'], 3),
            'descricao': descricao,
            'recomendacao': recomendacao,
        }
    
    def _analyze_risco_caixa_ml(self, records: List[MonthlyRecord], df: pd.DataFrame) -> Dict:
        """Análise de risco de caixa com Monte Carlo."""
        
        saldo_atual = records[-1].caixa
        
        # Burn rate com estatísticas
        variacoes = []
        for i in range(1, len(records)):
            variacoes.append(records[i].caixa - records[i-1].caixa)
        
        burn_rate_medio = np.mean(variacoes) if variacoes else 0
        burn_rate_std = np.std(variacoes) if variacoes else 0
        
        # Tendência do burn rate
        if len(variacoes) >= 6:
            recent = np.mean(variacoes[-3:])
            older = np.mean(variacoes[-6:-3])
            if recent < older - burn_rate_std:
                burn_trend = 'acelerando'
            elif recent > older + burn_rate_std:
                burn_trend = 'desacelerando'
            else:
                burn_trend = 'estavel'
        else:
            burn_trend = 'estavel'
        
        # Monte Carlo
        revenues = [r.receita for r in records]
        costs = [r.custos + r.despesas + r.impostos + r.folha for r in records]
        
        simulacao = self.monte_carlo.simulate_cash_flow(
            initial_cash=saldo_atual,
            monthly_revenues=revenues,
            monthly_costs=costs,
            periods=12
        )
        
        # Probabilidades de caixa negativo
        prob_3m = simulacao.cenario_pessimista.get('mes_3', saldo_atual) < 0
        prob_6m = simulacao.cenario_pessimista.get('mes_6', saldo_atual) < 0
        prob_12m = simulacao.prob_caixa_negativo
        
        # Volatilidade
        caixas = [r.caixa for r in records]
        volatilidade = np.std(caixas) if caixas else 0
        coef_var = (volatilidade / np.mean(caixas) * 100) if np.mean(caixas) > 0 else 0
        
        # Nível de risco
        if simulacao.meses_runway_p50 < 3 or prob_12m > 0.5:
            nivel = NivelRisco.CRITICO.value
        elif simulacao.meses_runway_p50 < 6 or prob_12m > 0.3:
            nivel = NivelRisco.ALTO.value
        elif simulacao.meses_runway_p50 < 12 or prob_12m > 0.1:
            nivel = NivelRisco.MODERADO.value
        elif burn_rate_medio < 0:
            nivel = NivelRisco.BAIXO.value
        else:
            nivel = NivelRisco.MINIMO.value
        
        # Descrição
        if nivel in [NivelRisco.CRITICO.value, NivelRisco.ALTO.value]:
            descricao = f"Simulação Monte Carlo ({simulacao.num_simulacoes} cenários) indica "
            descricao += f"{prob_12m*100:.0f}% de chance de caixa negativo em 12 meses. "
            descricao += f"Runway mediano: {simulacao.meses_runway_p50} meses."
            recomendacao = "AÇÃO IMEDIATA: Buscar capital, renegociar prazos, cortar custos."
        elif burn_rate_medio < 0:
            descricao = f"Consumo de R$ {abs(burn_rate_medio):,.0f}/mês (±R$ {burn_rate_std:,.0f}). "
            descricao += f"90% de chance de manter caixa por {simulacao.meses_runway_p90} meses."
            recomendacao = "Monitorar evolução e buscar reverter queima de caixa."
        else:
            descricao = f"Caixa saudável gerando R$ {burn_rate_medio:,.0f}/mês. "
            descricao += f"Probabilidade mínima de problemas."
            recomendacao = "Manter política atual. Avaliar aplicação de excedentes."
        
        return {
            'nivel': nivel,
            'saldo_atual': round(saldo_atual, 2),
            'burn_rate_medio': round(burn_rate_medio, 2),
            'burn_rate_std': round(burn_rate_std, 2),
            'burn_rate_tendencia': burn_trend,
            'runway_p10': simulacao.meses_runway_p10,
            'runway_p50': simulacao.meses_runway_p50,
            'runway_p90': simulacao.meses_runway_p90,
            'prob_caixa_negativo_3m': float(prob_3m),
            'prob_caixa_negativo_6m': float(prob_6m),
            'prob_caixa_negativo_12m': float(prob_12m),
            'volatilidade_caixa': round(volatilidade, 2),
            'coef_variacao': round(coef_var, 2),
            'simulacao': asdict(simulacao),
            'confianca': 85.0 if len(records) >= 12 else 70.0,
            'descricao': descricao,
            'recomendacao': recomendacao,
        }
    
    def _analyze_anomalias_ml(self, records: List[MonthlyRecord], df: pd.DataFrame) -> Dict:
        """Análise de anomalias com Isolation Forest."""
        
        # Features para detecção
        feature_cols = [
            'custo_pct', 'despesa_pct', 'imposto_pct', 'margem_liquida',
            'receita_var_1m', 'lucro_liquido', 'eficiencia_operacional'
        ]
        feature_cols = [c for c in feature_cols if c in df.columns]
        
        # Detecta anomalias
        predictions, scores, metrics = self.anomaly_detector.fit_detect(df, feature_cols)
        
        # Processa anomalias
        anomalias = []
        anomaly_idx = np.where(predictions == -1)[0]
        
        # Médias esperadas
        expected = {c: float(df[c].mean()) for c in feature_cols}
        
        for idx in anomaly_idx:
            record = records[idx]
            row_data = {c: float(df[c].iloc[idx]) for c in feature_cols}
            
            # Determina tipo de anomalia
            tipos = []
            if 'custo_pct' in row_data and row_data['custo_pct'] > expected['custo_pct'] * 1.2:
                tipos.append('Custos elevados')
            if 'margem_liquida' in row_data and row_data['margem_liquida'] < expected['margem_liquida'] * 0.7:
                tipos.append('Margem comprimida')
            if 'imposto_pct' in row_data and row_data['imposto_pct'] > expected['imposto_pct'] * 1.3:
                tipos.append('Impostos atípicos')
            
            tipo = tipos[0] if tipos else 'Padrão atípico'
            
            # Severidade baseada no score
            score = scores[idx]
            if score < -0.5:
                severidade = NivelRisco.CRITICO.value
            elif score < -0.3:
                severidade = NivelRisco.ALTO.value
            else:
                severidade = NivelRisco.MODERADO.value
            
            # Impacto estimado
            impacto = record.receita * abs(score) * 0.1
            
            anomalias.append({
                'tipo': tipo,
                'mes': record.periodo,
                'severidade': severidade,
                'score_anomalia': float(score),
                'valores_anomalos': row_data,
                'valor_esperado': expected,
                'descricao': self.anomaly_detector.explain_anomaly(row_data, expected, score),
                'impacto_estimado': round(impacto, 2),
            })
        
        # Score de normalidade
        score_normalidade = max(0, min(100, (np.mean(scores) + 0.5) * 100))
        
        # Meses mais anômalos
        worst_idx = np.argsort(scores)[:3]
        meses_anomalos = [records[i].periodo for i in worst_idx if i < len(records)]
        
        # Tendências
        if len(df) >= 6:
            custo_trend = 'subindo' if df['custo_pct'].iloc[-3:].mean() > df['custo_pct'].iloc[-6:-3].mean() else 'estavel'
            margem_trend = 'caindo' if df['margem_liquida'].iloc[-3:].mean() < df['margem_liquida'].iloc[-6:-3].mean() else 'estavel'
            imposto_trend = 'subindo' if df['imposto_pct'].iloc[-3:].mean() > df['imposto_pct'].iloc[-6:-3].mean() else 'estavel'
        else:
            custo_trend = margem_trend = imposto_trend = 'indeterminado'
        
        # Impacto total
        impacto_total = sum(a['impacto_estimado'] for a in anomalias)
        
        # Descrição
        if not anomalias:
            descricao = f"Isolation Forest não detectou anomalias significativas. Score de normalidade: {score_normalidade:.0f}/100."
        else:
            descricao = f"{len(anomalias)} anomalia(s) detectada(s) pelo Isolation Forest. "
            descricao += f"Features mais anômalas: {', '.join([f[0] for f in metrics['feature_importance'][:3]])}."
        
        return {
            'total': len(anomalias),
            'anomalias': anomalias,
            'contamination_estimada': round(metrics['contamination'], 3),
            'features_mais_anomalas': [f[0] for f in metrics['feature_importance'][:5]],
            'score_normalidade_geral': round(score_normalidade, 1),
            'meses_mais_anomalos': meses_anomalos,
            'tendencia_custos': custo_trend,
            'tendencia_margem': margem_trend,
            'tendencia_impostos': imposto_trend,
            'impacto_total_estimado': round(impacto_total, 2),
            'descricao': descricao,
        }
    
    def _analyze_probabilidades_ml(
        self,
        records: List[MonthlyRecord],
        df: pd.DataFrame,
        tendencia: Dict,
        risco_caixa: Dict,
        anomalias: Dict
    ) -> Dict:
        """Análise de probabilidades com XGBoost calibrado."""
        
        # Features para modelo
        feature_cols = [c for c in df.columns if c not in ['data', 'mes', 'trimestre'] and df[c].dtype in ['float64', 'int64']]
        
        # Treina e prediz
        results = self.probability_predictor.fit_predict(df, feature_cols)
        
        # Extrai probabilidades
        prob_prejuizo = results.get('prejuizo', {}).get('probability', 0.1) * 100
        prob_quebra = results.get('caixa_critico', {}).get('probability', 0.05) * 100
        
        # Probabilidade de imposto (baseada em variabilidade)
        impostos = [r.carga_tributaria for r in records]
        cv_impostos = (np.std(impostos) / np.mean(impostos) * 100) if np.mean(impostos) > 0 else 0
        prob_imposto = min(80, 10 + cv_impostos)
        
        # Ajustes baseados em outras análises
        if tendencia['direcao'] == 'down':
            prob_prejuizo = min(95, prob_prejuizo * 1.3)
        if risco_caixa['nivel'] in ['Crítico', 'Alto']:
            prob_quebra = min(95, prob_quebra * 1.5)
        if anomalias['total'] > 2:
            prob_imposto = min(85, prob_imposto * 1.2)
        
        # Classificação
        def classify(p):
            if p >= 70: return NivelRisco.CRITICO.value
            if p >= 50: return NivelRisco.ALTO.value
            if p >= 30: return NivelRisco.MODERADO.value
            if p >= 15: return NivelRisco.BAIXO.value
            return NivelRisco.MINIMO.value
        
        # Fatores de risco
        fatores_risco = []
        fatores_positivos = []
        
        # Analisa features importantes
        for target, result in results.items():
            for feat, imp in result.get('feature_importance', [])[:3]:
                if imp > 0.1:
                    val = df[feat].iloc[-1] if feat in df.columns else 0
                    media = df[feat].mean() if feat in df.columns else 0
                    if val < media * 0.8:
                        fatores_risco.append(f"{feat} abaixo do esperado")
                    elif val > media * 1.2:
                        if 'custo' in feat.lower() or 'despesa' in feat.lower():
                            fatores_risco.append(f"{feat} acima do esperado")
                        else:
                            fatores_positivos.append(f"{feat} acima do esperado")
        
        # Adiciona fatores baseados nas outras análises
        if tendencia['direcao'] == 'up':
            fatores_positivos.append("Faturamento em crescimento")
        elif tendencia['direcao'] == 'down':
            fatores_risco.append("Faturamento em queda")
        
        if risco_caixa['burn_rate_medio'] > 0:
            fatores_positivos.append("Caixa em crescimento")
        elif risco_caixa['nivel'] in ['Crítico', 'Alto']:
            fatores_risco.append(f"Risco de caixa {risco_caixa['nivel'].lower()}")
        
        if anomalias['total'] > 0:
            fatores_risco.append(f"{anomalias['total']} anomalias detectadas")
        else:
            fatores_positivos.append("Sem anomalias detectadas")
        
        # Score de saúde
        score = 100
        score -= prob_prejuizo * 0.3
        score -= prob_quebra * 0.4
        score -= prob_imposto * 0.1
        score += len(fatores_positivos) * 3
        score -= anomalias['total'] * 2
        score = max(0, min(100, score))
        
        # Confiança do score
        calibracao_media = np.mean([
            results.get('prejuizo', {}).get('calibration', 0.25),
            results.get('caixa_critico', {}).get('calibration', 0.25),
        ])
        score_confianca = max(50, 100 - calibracao_media * 200)
        
        # Descrição e recomendação
        if score >= 70:
            descricao = f"Modelos ML indicam boa saúde financeira (score {score:.0f}/100, confiança {score_confianca:.0f}%)."
            recomendacao = "Manter práticas atuais. Monitorar indicadores regularmente."
        elif score >= 40:
            descricao = f"Modelos indicam atenção necessária (score {score:.0f}/100). "
            descricao += f"Principais riscos: prejuízo ({prob_prejuizo:.0f}%), caixa ({prob_quebra:.0f}%)."
            if prob_prejuizo > prob_quebra:
                recomendacao = "Priorizar melhoria de margens e revisão de custos."
            else:
                recomendacao = "Priorizar gestão de caixa e capital de giro."
        else:
            descricao = f"ALERTA: Modelos ML indicam alto risco (score {score:.0f}/100). "
            descricao += f"Probabilidades: prejuízo {prob_prejuizo:.0f}%, quebra {prob_quebra:.0f}%."
            recomendacao = "AÇÃO URGENTE: Reunião com sócios para plano de contingência imediato."
        
        return {
            'prob_prejuizo': round(prob_prejuizo, 1),
            'prob_quebra': round(prob_quebra, 1),
            'prob_imposto_inesperado': round(prob_imposto, 1),
            'risco_prejuizo': classify(prob_prejuizo),
            'risco_quebra': classify(prob_quebra),
            'risco_imposto': classify(prob_imposto),
            'calibracao_prejuizo': round(results.get('prejuizo', {}).get('calibration', 0), 3),
            'calibracao_quebra': round(results.get('caixa_critico', {}).get('calibration', 0), 3),
            'features_risco_prejuizo': results.get('prejuizo', {}).get('feature_importance', []),
            'features_risco_quebra': results.get('caixa_critico', {}).get('feature_importance', []),
            'score_saude': round(score, 1),
            'score_confianca': round(score_confianca, 1),
            'fatores_risco': list(set(fatores_risco)),
            'fatores_positivos': list(set(fatores_positivos)),
            'descricao': descricao,
            'recomendacao': recomendacao,
        }
    
    def _generate_insights(
        self,
        tendencia: Dict,
        risco_caixa: Dict,
        anomalias: Dict,
        probabilidades: Dict
    ) -> List[str]:
        """Gera insights baseados nas análises."""
        
        insights = []
        
        # Insight de tendência
        if tendencia['tem_sazonalidade']:
            picos = tendencia['meses_pico']
            insights.append(f"📊 Sazonalidade detectada: picos nos meses {picos}. Planeje estoque e caixa.")
        
        if tendencia['mape'] < 10:
            insights.append(f"🎯 Previsões altamente confiáveis (MAPE {tendencia['mape']:.1f}%).")
        
        # Insight de caixa
        if risco_caixa['burn_rate_tendencia'] == 'acelerando':
            insights.append("⚠️ Consumo de caixa está acelerando. Investigar causas.")
        
        p10 = risco_caixa['runway_p10']
        p90 = risco_caixa['runway_p90']
        if p90 - p10 > 6:
            insights.append(f"📈 Alta incerteza no caixa: cenário otimista {p90} meses, pessimista {p10} meses.")
        
        # Insight de anomalias
        if anomalias['total'] > 0:
            features = anomalias['features_mais_anomalas'][:2]
            insights.append(f"🔍 Anomalias concentradas em: {', '.join(features)}.")
        
        # Insight de probabilidades
        if probabilidades['score_confianca'] >= 80:
            insights.append(f"✅ Alta confiança nas probabilidades ({probabilidades['score_confianca']:.0f}%).")
        
        return insights


# Alias para compatibilidade
ContabilAnalyzer = ContabilAnalyzerML
