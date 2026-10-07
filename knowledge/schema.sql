-- ====================================================================
-- ISKOM AI-OS DATABASE SCHEMA DEFINITION (DDL)
-- Dual-Layer Core Architecture: 16 Core Entities
-- ====================================================================

-- 1. USERS & ROLES
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('OWNER', 'MANAGER', 'STAFF') NOT NULL DEFAULT 'STAFF',
    phone VARCHAR(30) NULL,
    status ENUM('ACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. AGENTS REGISTRY
CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role_title VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) DEFAULT 'nous-hermes-3',
    temperature DECIMAL(3,2) DEFAULT 0.20,
    capabilities JSON NULL,
    status ENUM('ACTIVE', 'PAUSED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. CUSTOMERS
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(30) NOT NULL INDEX,
    email VARCHAR(150) NULL,
    customer_type ENUM('INDIVIDUAL', 'CORPORATE') DEFAULT 'INDIVIDUAL',
    identity_number VARCHAR(100) NULL COMMENT 'KTP or NPWP',
    address TEXT NULL,
    status ENUM('ACTIVE', 'BLOCKED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. LEADS & PIPELINE
CREATE TABLE IF NOT EXISTS leads (
    lead_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NULL,
    source ENUM('WEB_FORM', 'WHATSAPP', 'ADS', 'REFERRAL') DEFAULT 'WHATSAPP',
    requirement_summary TEXT NOT NULL,
    requested_units INT DEFAULT 1,
    pipeline_stage ENUM('NEW', 'QUALIFIED', 'NEGOTIATION', 'WON', 'LOST') DEFAULT 'NEW',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. PRODUCTS & LAPTOP CATALOG
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    brand VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    specs_cpu_ram_storage VARCHAR(255) NOT NULL,
    base_daily_rate DECIMAL(12,2) NOT NULL,
    base_monthly_rate DECIMAL(12,2) NOT NULL,
    min_deposit_idr DECIMAL(12,2) DEFAULT 200000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. PHYSICAL INVENTORY
CREATE TABLE IF NOT EXISTS inventory (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    asset_tag VARCHAR(50) UNIQUE NOT NULL,
    condition_status ENUM('READY_IN_WAREHOUSE', 'BOOKED', 'RENTED', 'MAINTENANCE', 'RETIRED') DEFAULT 'READY_IN_WAREHOUSE',
    current_location VARCHAR(100) DEFAULT 'Main Warehouse',
    last_qc_date DATE NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. APPROVALS (HUMAN-IN-THE-LOOP)
CREATE TABLE IF NOT EXISTS approvals (
    approval_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_code VARCHAR(50) UNIQUE NOT NULL,
    requester_agent_id VARCHAR(50) NOT NULL,
    trigger_rule_id VARCHAR(50) NOT NULL,
    category ENUM('DISCOUNT', 'REFUND', 'HIGH_VALUE', 'CUSTOM_TERMS') NOT NULL,
    payload_details JSON NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED') DEFAULT 'PENDING',
    decided_by_user_id INT NULL,
    decision_notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at DATETIME NULL,
    FOREIGN KEY (requester_agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (decided_by_user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. QUOTATIONS
CREATE TABLE IF NOT EXISTS quotations (
    quotation_id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_number VARCHAR(50) UNIQUE NOT NULL,
    lead_id INT NULL,
    customer_id INT NOT NULL,
    subtotal_amount DECIMAL(12,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    final_amount DECIMAL(12,2) NOT NULL,
    approval_id INT NULL,
    approval_status ENUM('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED') DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (approval_id) REFERENCES approvals(approval_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. RENTALS (ACTIVE CONTRACTS)
CREATE TABLE IF NOT EXISTS rentals (
    rental_id INT AUTO_INCREMENT PRIMARY KEY,
    rental_code VARCHAR(50) UNIQUE NOT NULL,
    quotation_id INT NULL,
    customer_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INT NOT NULL,
    deposit_amount DECIMAL(12,2) DEFAULT 0.00,
    rental_status ENUM('ACTIVE', 'EXTENDED', 'COMPLETED', 'OVERDUE') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quotation_id) REFERENCES quotations(quotation_id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. INVOICES
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    rental_id INT NOT NULL,
    customer_id INT NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    tax_ppn DECIMAL(12,2) DEFAULT 0.00,
    total_due DECIMAL(12,2) NOT NULL,
    due_date DATE NOT NULL,
    payment_status ENUM('UNPAID', 'PARTIAL', 'PAID', 'OVERDUE') DEFAULT 'UNPAID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    amount_paid DECIMAL(12,2) NOT NULL,
    payment_method ENUM('BANK_TRANSFER', 'CASH', 'PAYMENT_GATEWAY') DEFAULT 'BANK_TRANSFER',
    bank_reference VARCHAR(100) NULL,
    proof_file_path VARCHAR(255) NULL,
    verification_status ENUM('PENDING', 'VERIFIED', 'REJECTED') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. FOLLOW-UPS
CREATE TABLE IF NOT EXISTS follow_ups (
    follow_up_id INT AUTO_INCREMENT PRIMARY KEY,
    lead_id INT NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    channel ENUM('WHATSAPP', 'EMAIL', 'CALL') DEFAULT 'WHATSAPP',
    message_content TEXT NOT NULL,
    scheduled_at DATETIME NOT NULL,
    status ENUM('PENDING', 'SENT', 'FAILED') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. TICKETS (CUSTOMER SUPPORT)
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    rental_id INT NULL,
    issue_category ENUM('HARDWARE', 'SOFTWARE', 'BATTERY', 'ACCESSORY', 'DELIVERY') NOT NULL,
    priority ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT') DEFAULT 'MEDIUM',
    status ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED') DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. WORKFLOWS
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_name VARCHAR(100) NOT NULL,
    entity_type ENUM('LEAD', 'RENTAL', 'TICKET', 'INVOICE') NOT NULL,
    entity_id INT NOT NULL,
    current_step VARCHAR(50) NOT NULL,
    execution_state ENUM('RUNNING', 'WAITING_APPROVAL', 'COMPLETED', 'FAILED') DEFAULT 'RUNNING',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. KNOWLEDGE BASE
CREATE TABLE IF NOT EXISTS knowledge (
    doc_id INT AUTO_INCREMENT PRIMARY KEY,
    doc_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    category ENUM('SOP', 'FAQ', 'POLICY', 'PRICING') NOT NULL,
    content_markdown LONGTEXT NOT NULL,
    version VARCHAR(20) DEFAULT '1.0.0',
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 16. ACTIVITY LOGS (AUDIT TRAIL)
CREATE TABLE IF NOT EXISTS activity_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_uuid VARCHAR(64) NOT NULL INDEX,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_id VARCHAR(50) NOT NULL,
    user_id INT NULL,
    action_name VARCHAR(100) NOT NULL,
    tool_called VARCHAR(100) NULL,
    input_params JSON NULL,
    output_result JSON NULL,
    error_message TEXT NULL,
    latency_ms INT DEFAULT 0,
    tokens_used INT DEFAULT 0,
    status ENUM('SUCCESS', 'BLOCKED_BY_RULE', 'FAILED') DEFAULT 'SUCCESS',
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
