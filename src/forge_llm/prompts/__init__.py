"""
ForgeLLM Prompts - Carregamento de prompts customizáveis.

Módulo para carregar prompts de arquivos markdown.

Uso:
    from forge_llm.prompts import load_prompt, get_prompts_path

    # Carregar prompt de sumarização
    prompt = load_prompt("summarization")

    # Carregar system prompt
    system = load_prompt("system/coding_assistant")

    # Obter caminho para pasta de prompts
    path = get_prompts_path()
"""
import re
from pathlib import Path
from typing import Optional


def get_prompts_path() -> Path:
    """
    Obter caminho para diretório de prompts.

    Returns:
        Path: Caminho para pasta prompts/ na raiz do projeto

    Usage:
        from forge_llm.prompts import get_prompts_path
        prompts_dir = get_prompts_path()
    """
    # Navigate from src/forge_llm/prompts/__init__.py to project root/prompts
    # Path(__file__).parent = {project}/src/forge_llm/prompts
    # .parent = {project}/src/forge_llm
    # .parent.parent = {project}/src
    # .parent.parent.parent = {project} (root)
    current = Path(__file__).resolve().parent  # {project}/src/forge_llm/prompts
    project_root = current.parent.parent.parent  # {project}
    return project_root / "prompts"


def load_prompt(name: str, extract_code_block: bool = True) -> str:
    """
    Carregar prompt de arquivo markdown.

    Args:
        name: Nome do prompt (sem extensão .md)
              Ex: "summarization", "system/coding_assistant"
        extract_code_block: Se True, extrai apenas o conteúdo do primeiro
                           bloco de código. Se False, retorna arquivo inteiro.

    Returns:
        str: Conteúdo do prompt

    Raises:
        FileNotFoundError: Se arquivo não existir

    Usage:
        from forge_llm.prompts import load_prompt

        # Carregar prompt de sumarização
        prompt = load_prompt("summarization")

        # Carregar sem extrair code block
        full_doc = load_prompt("summarization", extract_code_block=False)
    """
    prompts_path = get_prompts_path()
    file_path = prompts_path / f"{name}.md"

    if not file_path.exists():
        raise FileNotFoundError(f"Prompt not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    if extract_code_block:
        return _extract_first_code_block(content)

    return content


def load_prompt_from_file(file_path: str | Path, extract_code_block: bool = True) -> str:
    """
    Carregar prompt de arquivo customizado.

    Args:
        file_path: Caminho para arquivo de prompt
        extract_code_block: Se True, extrai apenas o primeiro bloco de código

    Returns:
        str: Conteúdo do prompt

    Usage:
        from forge_llm.prompts import load_prompt_from_file

        # Carregar de arquivo customizado
        prompt = load_prompt_from_file("my_prompts/custom.md")
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    content = path.read_text(encoding="utf-8")

    if extract_code_block:
        return _extract_first_code_block(content)

    return content


def list_prompts() -> list[str]:
    """
    Listar todos os prompts disponíveis.

    Returns:
        list[str]: Lista de nomes de prompts disponíveis

    Usage:
        from forge_llm.prompts import list_prompts

        prompts = list_prompts()
        # ['summarization', 'extraction', 'system/coding_assistant', ...]
    """
    prompts_path = get_prompts_path()

    if not prompts_path.exists():
        return []

    prompts = []
    for md_file in prompts_path.rglob("*.md"):
        if md_file.name == "README.md":
            continue
        # Convert path to prompt name
        relative = md_file.relative_to(prompts_path)
        name = str(relative.with_suffix(""))
        prompts.append(name)

    return sorted(prompts)


def _extract_first_code_block(content: str) -> str:
    """
    Extrair conteúdo do primeiro bloco de código markdown.

    Args:
        content: Conteúdo markdown

    Returns:
        str: Conteúdo do bloco de código, ou conteúdo original se não houver bloco
    """
    # Pattern para bloco de código markdown
    pattern = r"```(?:\w*)\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()

    # Se não encontrar bloco de código, retorna conteúdo após primeiro heading
    lines = content.split("\n")
    content_lines = []
    found_heading = False

    for line in lines:
        if line.startswith("# ") and not found_heading:
            found_heading = True
            continue
        if found_heading:
            content_lines.append(line)

    return "\n".join(content_lines).strip() if content_lines else content


# Prompts padrão embutidos (fallback se arquivos não existirem)
DEFAULT_PROMPTS = {
    "summarization": """Summarize the following conversation concisely.
Focus on key information, decisions made, and important context.
Keep the summary brief but preserve essential details.

Conversation:
{messages}

Summary:""",

    "system/general_assistant": """You are a helpful, harmless, and honest assistant.
Be concise but thorough. Admit when you don't know something.
Ask clarifying questions when needed.""",
}


def get_default_prompt(name: str) -> str | None:
    """
    Obter prompt padrão embutido (fallback).

    Args:
        name: Nome do prompt

    Returns:
        str ou None: Prompt padrão ou None se não existir
    """
    return DEFAULT_PROMPTS.get(name)


__all__ = [
    "get_prompts_path",
    "load_prompt",
    "load_prompt_from_file",
    "list_prompts",
    "get_default_prompt",
    "DEFAULT_PROMPTS",
]
