#!/usr/bin/env python3
"""
compress_soul.py — Genera versiones comprimidas de los SOUL.md por tier.

Uso:
    python scripts/compress_soul.py --input agents/SOUL-minecraft.md --output agents/casts/.soul_cache/eko_CORE.md --tier CORE --type "Manifestor 4/6"
    python scripts/compress_soul.py --input agents/casts/landfolk/stevie.md --output agents/casts/.soul_cache/stevie_MINI.md --tier MINI --type "Manifestor"

Tiers:
    FULL — Sin cambios (para Pamplinas)
    CORE — 30% del original: identidad + tipo HD + estrategia + voz + reglas
    MINI — 10% del original: nombre + tipo + estrategia en una línea + voz
"""

import argparse
import re
from pathlib import Path


def extract_section(text: str, heading: str) -> str:
    """Extract a markdown section by heading."""
    pattern = rf"(^|\n)(#{{1,3}})\s+{re.escape(heading)}.*?\n(?=#{{1,3}}\s|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(0).strip() if match else ""


def extract_between_headings(text: str, start_heading: str, end_heading: str = None) -> str:
    """Extract content between two headings."""
    start_pattern = rf"(^|\n)(#{{1,3}})\s+{re.escape(start_heading)}.*?\n"
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    if not start_match:
        return ""
    
    start_idx = start_match.start()
    
    if end_heading:
        end_pattern = rf"\n(#{{1,3}})\s+{re.escape(end_heading)}"
        end_match = re.search(end_pattern, text[start_idx + 1:], re.IGNORECASE)
        if end_match:
            end_idx = start_idx + 1 + end_match.start()
            return text[start_idx:end_idx].strip()
    
    # If no end heading, take until next same-level heading
    level = start_match.group(2)  # the ## part
    next_heading = rf"\n{level}\s+"
    next_match = re.search(next_heading, text[start_idx + 1:])
    if next_match:
        end_idx = start_idx + 1 + next_match.start()
        return text[start_idx:end_idx].strip()
    
    return text[start_idx:].strip()


def compress_full(text: str) -> str:
    """No compression."""
    return text


def compress_core(text: str, soul_type: str = "") -> str:
    """Compress to ~30%: identity, HD type, strategy, voice, golden rules, Minecraft behavior."""
    sections = []
    
    # Extract identity/name
    name_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if name_match:
        sections.append(f"# {name_match.group(1)}")
    
    # HD type info
    hd_match = re.search(r"##?\s*(Human Design|Type|Profile|Authority|Strategy).*?\n", text, re.IGNORECASE)
    if hd_match:
        type_section = extract_between_headings(text, hd_match.group(0).strip().lstrip("#").strip())
        if type_section:
            sections.append(type_section)
    
    # Strategy
    strategy = extract_section(text, "Strategy")
    if strategy:
        sections.append(strategy)
    
    # Voice
    voice = extract_section(text, "Voice")
    if voice:
        sections.append(voice)
    
    # Golden rules / important directives
    rules = extract_section(text, "Golden")
    if rules:
        sections.append(rules)
    
    # Minecraft behavior
    mc = extract_section(text, "Minecraft")
    if mc:
        sections.append(mc)
    
    # If we couldn't extract sections, fall back to first 30% of lines
    if not sections:
        lines = text.split("\n")
        cutoff = max(30, len(lines) // 3)
        return "\n".join(lines[:cutoff])
    
    result = "\n\n".join(sections)
    # Add compression notice
    result += f"\n\n[SOUL compressed to CORE tier for Gemma context optimization. Type: {soul_type}]"
    return result


def compress_mini(text: str, soul_type: str = "") -> str:
    """Compress to ~10%: one-liner identity + strategy + voice."""
    # Extract name
    name_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    name = name_match.group(1) if name_match else "Bot"
    
    # Extract type from HD line
    type_match = re.search(r"(?:Type|Human Design)[\s:]+([^\n]+)", text, re.IGNORECASE)
    hd_type = type_match.group(1).strip() if type_match else soul_type
    
    # Extract strategy one-liner
    strategy_match = re.search(r"Strategy[\s:]+([^\n]+)", text, re.IGNORECASE)
    strategy = strategy_match.group(1).strip() if strategy_match else "Respond to life"
    
    # Extract voice style
    voice_match = re.search(r"Voice[\s:]+([^\n]+)", text, re.IGNORECASE)
    voice = voice_match.group(1).strip() if voice_match else "natural"
    
    # Extract signature phrase if any
    phrase_match = re.search(r'"([^"]{10,80})"', text)
    phrase = phrase_match.group(1) if phrase_match else ""
    
    lines = [
        f"# {name}",
        f"",
        f"You are {name}, a {hd_type}. Your strategy: {strategy}. Voice: {voice}.",
    ]
    
    if phrase:
        lines.append(f'Signature phrase: "{phrase}"')
    
    lines.append(f"[SOUL compressed to MINI tier for Gemma context optimization.]")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compress SOUL.md files for Gemma context optimization")
    parser.add_argument("--input", required=True, help="Input SOUL.md path")
    parser.add_argument("--output", required=True, help="Output compressed path")
    parser.add_argument("--tier", choices=["FULL", "CORE", "MINI"], required=True, help="Compression tier")
    parser.add_argument("--type", default="", help="Human Design type (e.g. 'Manifestor 4/6')")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return 1
    
    text = input_path.read_text(encoding="utf-8")
    
    if args.tier == "FULL":
        compressed = compress_full(text)
    elif args.tier == "CORE":
        compressed = compress_core(text, args.type)
    else:
        compressed = compress_mini(text, args.type)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(compressed, encoding="utf-8")
    
    original_tokens = len(text) // 3.5  # rough estimate
    compressed_tokens = len(compressed) // 3.5
    reduction = (1 - compressed_tokens / original_tokens) * 100
    
    print(f"Compressed: {input_path} -> {output_path}")
    print(f"  Tier: {args.tier}")
    print(f"  Original: ~{original_tokens:.0f} tokens")
    print(f"  Compressed: ~{compressed_tokens:.0f} tokens")
    print(f"  Reduction: {reduction:.0f}%")
    
    return 0


if __name__ == "__main__":
    exit(main())
