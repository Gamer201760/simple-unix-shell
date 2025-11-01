from pathlib import Path

from entity.context import CommandContext


def expand_user_with_ctx(raw: str, ctx: CommandContext) -> str:
    if raw == '~' or raw.startswith('~/'):
        return ctx.home + raw[1:]
    prefix = f'~{ctx.user}'
    if raw == prefix or raw.startswith(prefix + '/'):
        return ctx.home + raw[len(prefix) :]
    return raw


def normalize(raw: str, ctx: CommandContext) -> Path:
    expanded = expand_user_with_ctx(raw, ctx)
    p = Path(expanded)
    if not p.is_absolute():
        p = Path(ctx.pwd) / p
    return p.resolve(strict=False)
