"""Add Profile model

Revision ID: 3b703d5da017
Revises: 5bfb2f664b04
Create Date: 2025-08-21 13:15:00.366797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b703d5da017'
down_revision: Union[str, Sequence[str], None] = '5bfb2f664b04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # A) Create profiles if missing (raw SQL for IF NOT EXISTS compatibility)
    op.execute("""
    create table if not exists public.profiles (
      id uuid primary key references auth.users(id) on delete cascade,
      username text unique,
      created_at timestamptz default now()
    );
    """)

    # B) Ensure user_id exists and is UUID
    # add column if missing
    op.execute("""
    do $$
    begin
      if not exists (
        select 1 from information_schema.columns
        where table_schema='public' and table_name='chat_session' and column_name='user_id'
      ) then
        alter table public.chat_session add column user_id uuid not null;
      end if;
    end$$;
    """)

    # alter type to uuid if needed
    op.execute("""
    do $$
    begin
      if exists (
        select 1 from information_schema.columns
        where table_schema='public' and table_name='chat_session' and column_name='user_id'
          and data_type <> 'uuid'
      ) then
        alter table public.chat_session
          alter column user_id type uuid using user_id::uuid;
      end if;
    end$$;
    """)

    # C) Drop old FK (if any) and add FK to profiles
    op.execute("""
    do $$
    begin
      if exists (
        select 1 from pg_constraint
        where conname = 'chat_session_user_id_fkey'
          and conrelid = 'public.chat_session'::regclass
      ) then
        alter table public.chat_session drop constraint chat_session_user_id_fkey;
      end if;

      alter table public.chat_session
        add constraint chat_session_user_id_fkey
          foreign key (user_id) references public.profiles(id) on delete cascade;
    end$$;
    """)

    # D) Composite index
    op.execute("""
    create index if not exists ix_chat_session_user_lastused
      on public.chat_session (user_id, last_used);
    """)

def downgrade():
    # Best-effort revert: drop FK and index; keep profiles table (non-destructive)
    op.execute("""
    do $$
    begin
      if exists (
        select 1 from pg_constraint
        where conname = 'chat_session_user_id_fkey'
          and conrelid = 'public.chat_session'::regclass
      ) then
        alter table public.chat_session drop constraint chat_session_user_id_fkey;
      end if;
    end$$;
    """)
    op.execute("drop index if exists ix_chat_session_user_lastused;")
    # not dropping profiles to avoid losing data