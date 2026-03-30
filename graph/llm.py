import os
from typing import Any

import yaml
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

# 환경 변수 로드
load_dotenv()


class LLMManager:
    """복수개의 LLM 인스턴스를 관리하고 설정에 따라 생성하는 클래스"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.models_config = self.config.get("models", {})
        self.llm_cfg = self.config.get("llm_config", {})
        self._instances: dict[str, Any] = {}

    def _load_config(self) -> dict[str, Any]:
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, encoding="utf-8") as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get_model(self, role: str) -> Any:
        """역할에 따른 모델 인스턴스 반환

        Args:
            role: llm_config에 정의된 역할 키 (예: 'analysis_model', 'report_model')

        """
        model_key = self.llm_cfg.get(role)
        if not model_key:
            # 노드별 기본값 제공 (설정 누락 시 대비)
            defaults = {
                "market_analysis_model": "qwen_cloud",
                "stock_analysis_model": "minimax_cloud",
                "report_generation_model": "gpt_oss_cloud",
            }
            model_key = defaults.get(role)
            if not model_key:
                raise ValueError(
                    f"Role '{role}' is not defined in llm_config and no default exists"
                )

        # 이미 생성된 인스턴스가 있으면 반환 (캐싱)
        if model_key in self._instances:
            return self._instances[model_key]

        model_info = self.models_config.get(model_key)
        if not model_info:
            raise ValueError(
                f"Model '{model_key}' is not defined in models section of config.yaml"
            )

        instance = self._create_instance(model_info)
        self._instances[model_key] = instance
        return instance

    def _create_instance(self, info: dict[str, Any]) -> Any:
        """설정 정보를 바탕으로 실제 LLM 객체 생성"""
        provider = info.get("provider")
        name = info.get("name")
        base_url = info.get("base_url")

        # 모델별 개별 설정 우선, 없으면 공통 설정 적용
        temperature = info.get("temperature") or self.llm_cfg.get("temperature", 0.1)
        num_ctx = info.get("num_ctx") or self.llm_cfg.get("num_ctx", 65536)

        if provider == "ollama":
            return ChatOllama(
                model=name, base_url=base_url, temperature=temperature, num_ctx=num_ctx
            )
        elif provider == "openrouter":
            return ChatOpenAI(
                model=name,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=base_url or "https://openrouter.ai/api/v1",
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# 전역 매니저 인스턴스 생성
llm_manager = LLMManager()
