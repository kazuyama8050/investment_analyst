create database if not exists investment_analyst;

create table investment_analyst.symbols (
    symbol varchar(50) primary key,
    name varchar(255) not null,
    country varchar(50) not null,
    market varchar(50) not null,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    index symbol_index (symbol)
);


create table investment_analyst.symbol_finances (
    symbol varchar(50) primary key,
    latest_closing_date date not null default "1970-01-01",
    is_valid tinyint(4) not null default 0,
    four_quarters_eps float,
    three_quarters_eps float,
    two_quarters_eps float,
    latest_quarter_eps float,
    four_quarters_revenue int unsigned,
    three_quarters_revenue int unsigned,
    two_quarters_revenue int unsigned,
    latest_quarter_revenue int unsigned,
    four_years_eps float,
    three_years_eps float,
    two_years_eps float,
    latest_year_eps float,
    latest_year_roe float,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    index symbol_index (symbol)
);

create table investment_analyst.symbol_stocks (
    symbol varchar(50) primary key,
    is_valid tinyint(4) not null default 0,
    c float,
    c63 float,
    c126 float,
    c189 float,
    c252 float,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    index symbol_index (symbol)
);