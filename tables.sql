DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

CREATE TYPE symbol as ENUM ('ADD', 'SUB', 'MUL', 'DIV', 'AQ', 'POWER', 'POWERABS',
  'ABS', 'ACOS', 'ASIN', 'ATAN', 'ATAN2', 'CEIL', 'COS', 'COSH', 'EXP',
  'FLOOR', 'LN', 'LOG10', 'MOD', 'SIN', 'SINH', 'SQRT',
  'TAN', 'TANH', 'CONST', 'PARAM', 'VAR');

-- create a type composed of either an operator_symbol with two integers, a function symbol with one integer or a consant_symbol with one value
CREATE TYPE enode AS (
    op symbol,
    left_c INTEGER,
    right_c INTEGER,
    value NUMERIC
);

CREATE TABLE canonical_map (
  from_eid INTEGER PRIMARY KEY,
  to_eid INTEGER NOT NULL
);

CREATE TABLE enode_map (
    enode enode PRIMARY KEY,
    eid BIGSERIAL
);
CREATE INDEX eid_idx ON enode_map (eid);

CREATE TABLE eclass (
    eid INTEGER PRIMARY KEY,
    height INTEGER NOT NULL,
    size INTEGER NOT NULL,
    cost NUMERIC NOT NULL,
    best enode NOT NULL
);
