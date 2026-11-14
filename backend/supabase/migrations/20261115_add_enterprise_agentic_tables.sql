-- Migration: Enterprise Agentic Support Tables
-- Customers table
create table if not exists customers (
  id bigint generated always as identity primary key,
  email text not null unique,
  name text not null,
  loyalty_tier text not null default 'standard' check (loyalty_tier in ('standard', 'vip', 'premium')),
  churn_risk_score real default 0.1,
  created_at timestamptz not null default now()
);

-- Orders table
create table if not exists orders (
  order_id text primary key,
  customer_email text not null references customers (email) on delete cascade,
  purchase_date timestamptz not null,
  model text not null,
  status text not null default 'delivered' check (status in ('processing', 'shipped', 'transit', 'delivered', 'returned', 'cancelled')),
  serial_number text,
  carrier text,
  tracking_number text,
  warranty_end_date timestamptz not null,
  created_at timestamptz not null default now()
);

create index if not exists orders_customer_email_idx on orders (customer_email);

-- Order Items table
create table if not exists order_items (
  id bigint generated always as identity primary key,
  order_id text not null references orders (order_id) on delete cascade,
  sku text not null,
  title text not null,
  unit_price_cents int not null,
  is_accessory boolean not null default false
);

create index if not exists order_items_order_id_idx on order_items (order_id);

-- RMA Requests table
create table if not exists rma_requests (
  rma_id text primary key,
  order_id text not null references orders (order_id) on delete cascade,
  customer_email text not null,
  status text not null default 'label_generated' check (status in ('pending', 'label_generated', 'received', 'inspected', 'completed', 'rejected')),
  reason text not null,
  return_label_url text not null,
  created_at timestamptz not null default now()
);

create index if not exists rma_order_id_idx on rma_requests (order_id);

-- Approvals table (Human-in-the-Loop)
create table if not exists approvals (
  id uuid primary key default gen_random_uuid(),
  thread_id text not null,
  action_type text not null,
  payload jsonb not null default '{}',
  status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  proposed_reply text,
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolved_by text
);

create index if not exists approvals_thread_id_idx on approvals (thread_id);
create index if not exists approvals_status_idx on approvals (status);

-- Enable RLS
alter table customers enable row level security;
alter table orders enable row level security;
alter table order_items enable row level security;
alter table rma_requests enable row level security;
alter table approvals enable row level security;

