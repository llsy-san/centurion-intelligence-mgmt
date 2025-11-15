-- 定时任务服务数据库初始化脚本

-- 创建订单同步表
CREATE TABLE IF NOT EXISTS order_sync (
    order_no VARCHAR(50) PRIMARY KEY,
    external_no VARCHAR(100) NOT NULL UNIQUE,
    external_order_status VARCHAR(50),
    order_type VARCHAR(20) DEFAULT 'WEMINI',
    tenant_id VARCHAR(50) DEFAULT 'default',
    tenant_name VARCHAR(100) DEFAULT '默认',
    customer_id VARCHAR(100),
    create_time TIMESTAMP WITH TIME ZONE,
    pay_type VARCHAR(20) DEFAULT 'WECHAT',
    pay_time TIMESTAMP WITH TIME ZONE,
    arrival_time TIMESTAMP WITH TIME ZONE,
    pay_status VARCHAR(20),
    order_status VARCHAR(20),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pay_no VARCHAR(100),
    mailing_address TEXT,
    mailing_status VARCHAR(50),
    hotel_confirm_no VARCHAR(100),
    product_count INTEGER DEFAULT 0,
    avg_price DECIMAL(10, 2) DEFAULT 0,
    order_amount DECIMAL(10, 2) DEFAULT 0,
    refund_amount DECIMAL(10, 2) DEFAULT 0,
    settlement_amount DECIMAL(10, 2) DEFAULT 0,
    channel_fee DECIMAL(10, 2) DEFAULT 0,
    sync_status VARCHAR(20) DEFAULT 'PENDING',
    sync_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_order_sync_external_no ON order_sync(external_no);
CREATE INDEX IF NOT EXISTS idx_order_sync_customer_id ON order_sync(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_sync_order_status ON order_sync(order_status);
CREATE INDEX IF NOT EXISTS idx_order_sync_create_time ON order_sync(create_time);
CREATE INDEX IF NOT EXISTS idx_order_sync_tenant_id ON order_sync(tenant_id);

-- 创建订单产品同步表
CREATE TABLE IF NOT EXISTS order_product_sync (
    id SERIAL PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL REFERENCES order_sync(order_no),
    product_id VARCHAR(50) DEFAULT 'default',
    product_name VARCHAR(200) DEFAULT '默认',
    tenant_id VARCHAR(50) DEFAULT 'default',
    tenant_name VARCHAR(100) DEFAULT '默认',
    external_no VARCHAR(100) NOT NULL,
    category_level1 VARCHAR(100) DEFAULT '南京夫子庙',
    category_level2 VARCHAR(100),
    category_level3 VARCHAR(100),
    category_level4 VARCHAR(100) DEFAULT '联票',
    category_level5 VARCHAR(100),
    channel_price DECIMAL(10, 2),
    channel_commission_rate DECIMAL(5, 4) DEFAULT 0.0038,
    available_start_time TIMESTAMP WITH TIME ZONE,
    available_end_time TIMESTAMP WITH TIME ZONE,
    channel_id VARCHAR(50),
    channel_name VARCHAR(100) DEFAULT '微信小程序',
    quantity INTEGER DEFAULT 1,
    user_no VARCHAR(100),
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    customer_id_card VARCHAR(50),
    flexible_collection DECIMAL(10, 2),
    product_status VARCHAR(20),
    verify_method VARCHAR(20),
    verify_device VARCHAR(50) DEFAULT '扫码机',
    verify_device_name VARCHAR(100),
    verify_id VARCHAR(100),
    refund_device_name VARCHAR(100),
    refund_account_id VARCHAR(100),
    refund_device VARCHAR(50),
    refund_method VARCHAR(20),
    apply_refund_amount DECIMAL(10, 2),
    actual_refund_amount DECIMAL(10, 2),
    refund_status VARCHAR(20),
    refund_no VARCHAR(100),
    refund_reason VARCHAR(200),
    refund_time TIMESTAMP WITH TIME ZONE,
    use_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    mailing_address TEXT,
    express_no VARCHAR(100),
    refund_address TEXT,
    refund_express_no VARCHAR(100),
    channel_product_commission DECIMAL(10, 2)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_order_product_sync_order_no ON order_product_sync(order_no);
CREATE INDEX IF NOT EXISTS idx_order_product_sync_external_no ON order_product_sync(external_no);
CREATE INDEX IF NOT EXISTS idx_order_product_sync_customer_phone ON order_product_sync(customer_phone);
CREATE INDEX IF NOT EXISTS idx_order_product_sync_product_status ON order_product_sync(product_status);
CREATE INDEX IF NOT EXISTS idx_order_product_sync_created_at ON order_product_sync(created_at);

-- 创建产品明细表
CREATE TABLE IF NOT EXISTS product_detail (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category_level1 VARCHAR(100),
    category_level2 VARCHAR(100),
    category_level3 VARCHAR(100),
    category_level4 VARCHAR(100),
    category_level5 VARCHAR(100),
    product_price DECIMAL(10, 2),
    product_attrs JSONB,
    purchase_time TIMESTAMP WITH TIME ZONE,
    available_time TIMESTAMP WITH TIME ZONE,
    product_spec VARCHAR(500),
    tenant_id VARCHAR(50),
    tenant_name VARCHAR(100),
    inventory INTEGER DEFAULT 0,
    tags VARCHAR(500),
    del_yn VARCHAR(1) DEFAULT 'N',
    remarks TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建组织表
CREATE TABLE IF NOT EXISTS organization (
    org_id VARCHAR(50) PRIMARY KEY,
    org_name VARCHAR(200) NOT NULL,
    org_type VARCHAR(50),
    customer_name VARCHAR(100),
    unique_id VARCHAR(100),
    channel_user_id VARCHAR(100),
    contact_info VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    province VARCHAR(50),
    city VARCHAR(50),
    source_channel VARCHAR(100),
    tags VARCHAR(500),
    remarks TEXT,
    total_consume_count INTEGER DEFAULT 0,
    total_consume_amount DECIMAL(10, 2) DEFAULT 0,
    activation_time TIMESTAMP WITH TIME ZONE,
    first_consume_time TIMESTAMP WITH TIME ZONE
);

-- 创建同步任务日志表
CREATE TABLE IF NOT EXISTS sync_task_log (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sync_task_log_task_name ON sync_task_log(task_name);
CREATE INDEX IF NOT EXISTS idx_sync_task_log_created_at ON sync_task_log(created_at);
CREATE INDEX IF NOT EXISTS idx_sync_task_log_status ON sync_task_log(status);

-- 插入一些示例数据
INSERT INTO product_detail (product_id, product_name, category_level1, category_level4, product_price, tenant_id, tenant_name) 
VALUES 
    ('default', '默认产品', '南京夫子庙', '联票', 0.00, 'default', '默认'),
    ('nj_fuzimiao_01', '南京夫子庙联票', '南京夫子庙', '联票', 88.00, 'default', '默认')
ON CONFLICT (product_id) DO NOTHING;

-- 创建订单编号序列
CREATE SEQUENCE IF NOT EXISTS order_no_seq START WITH 1;