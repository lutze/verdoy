# VerdoyLab Platform - Mental Models & Information Architecture

## 🏗️ Core Entity Hierarchy

### **Level 1: Foundation Entities**
```
┌─────────────────┐    ┌─────────────────┐
│   Organization  │    │      User       │
│   (Container)   │    │   (Member)      │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │ Membership  │
              │ (Many-Many) │
              └─────────────┘
```

### **Level 2: Work Organization**
```
┌─────────────────┐    ┌─────────────────┐
│     Project     │    │    Process      │
│   (Container)   │    │  (Template)     │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │  Process    │
              │ Assignment  │
              └─────────────┘
```

### **Level 3: Execution & Tools**
```
┌─────────────────┐    ┌─────────────────┐
│   Experiment    │    │      Tool       │
│   (Execution)   │    │  (Bioreactor)   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │   Tool      │
              │ Usage       │
              └─────────────┘
```

### **Level 4: Hardware Components**
```
┌─────────────────┐    ┌─────────────────┐
│   Tool          │    │   Sensor/       │
│  Controller     │    │  Actuator       │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │ Hardware    │
              │ Connection  │
              └─────────────┘
```

## 📋 Detailed Relationship Model

### **1. Organization & User Management**

#### **Organization Structure**
```sql
-- Organizations (Level 1 Container)
CREATE TABLE entities (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL, -- 'organization'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    properties JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Organization Members (Many-Many)
CREATE TABLE organization_members (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES entities(id),
    user_id UUID REFERENCES entities(id),
    role VARCHAR(50) NOT NULL, -- 'admin', 'member', 'viewer'
    is_primary BOOLEAN DEFAULT FALSE, -- Primary organization for user
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);
```

#### **User Membership Rules**
- **Multi-Organization Support**: Users can belong to multiple organizations
- **Primary Organization**: Each user has one primary organization (for default context)
- **Role-Based Access**: Admin, Member, Viewer roles within each organization
- **Minimum Membership**: Users must belong to at least one organization

### **2. Project & Process Management**

#### **Project Structure**
```sql
-- Projects (Level 2 Container)
CREATE TABLE entities (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL, -- 'project'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES entities(id), -- Primary organization
    properties JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active'
);

-- Project Organizations (Many-Many)
CREATE TABLE project_organizations (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES entities(id),
    organization_id UUID REFERENCES entities(id),
    relationship_type VARCHAR(50) NOT NULL, -- 'primary', 'collaborator', 'viewer'
    UNIQUE(project_id, organization_id)
);
```

#### **Process Structure**
```sql
-- Processes (Templates)
CREATE TABLE processes (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    process_type VARCHAR(100) NOT NULL, -- 'fermentation', 'cultivation', etc.
    definition JSONB NOT NULL, -- Steps, parameters, tool requirements
    organization_id UUID REFERENCES entities(id),
    is_template BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Process Sharing (Many-Many)
CREATE TABLE process_sharing (
    id UUID PRIMARY KEY,
    process_id UUID REFERENCES processes(id),
    organization_id UUID REFERENCES entities(id),
    access_level VARCHAR(50) NOT NULL, -- 'read', 'write', 'admin'
    UNIQUE(process_id, organization_id)
);
```

### **3. Experiment & Trial Management**

#### **Experiment Structure**
```sql
-- Experiments (Execution Context)
CREATE TABLE experiments (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    project_id UUID REFERENCES entities(id),
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'active', 'completed', 'archived'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Experiment Trials (Execution Instances)
CREATE TABLE experiment_trials (
    id UUID PRIMARY KEY,
    experiment_id UUID REFERENCES experiments(id),
    trial_number INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    UNIQUE(experiment_id, trial_number)
);
```

### **4. Tool & Hardware Management**

#### **Tool Structure**
```sql
-- Tools (Bioreactors)
CREATE TABLE entities (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL, -- 'device.bioreactor'
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES entities(id), -- Owner
    properties JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'offline'
);

-- Tool Controllers
CREATE TABLE tool_controllers (
    id UUID PRIMARY KEY,
    tool_id UUID REFERENCES entities(id),
    controller_type VARCHAR(100) NOT NULL, -- 'esp32', 'raspberry_pi', etc.
    mac_address VARCHAR(17),
    firmware_version VARCHAR(50),
    status VARCHAR(50) DEFAULT 'offline'
);

-- Sensors & Actuators
CREATE TABLE hardware_components (
    id UUID PRIMARY KEY,
    controller_id UUID REFERENCES tool_controllers(id),
    component_type VARCHAR(50) NOT NULL, -- 'sensor', 'actuator'
    component_name VARCHAR(100) NOT NULL, -- 'temperature', 'ph', 'pump', 'heater'
    unique_id UUID NOT NULL, -- Unique identifier for physical component
    properties JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active'
);
```

## 🔧 Relationship Rules & Constraints

### **1. Organization & User Rules**
```python
# User must belong to at least one organization
def validate_user_membership(user_id: UUID) -> bool:
    return db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id
    ).count() > 0

# User can have multiple organizations but one primary
def get_user_primary_organization(user_id: UUID) -> Optional[Organization]:
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.is_primary == True
    ).first()
    return member.organization if member else None
```

### **2. Project & Process Rules**
```python
# Project has one primary organization (owner)
def get_project_primary_organization(project_id: UUID) -> Organization:
    project = db.query(Entity).filter(
        Entity.id == project_id,
        Entity.entity_type == 'project'
    ).first()
    return project.organization

# Process can be shared across organizations
def get_shared_processes(organization_id: UUID) -> List[Process]:
    return db.query(Process).join(ProcessSharing).filter(
        ProcessSharing.organization_id == organization_id
    ).all()
```

### **3. Experiment & Trial Rules**
```python
# Experiment belongs to exactly one project
def validate_experiment_project(experiment_id: UUID, project_id: UUID) -> bool:
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()
    return experiment.project_id == project_id

# Trial numbers must be unique within experiment
def get_next_trial_number(experiment_id: UUID) -> int:
    max_trial = db.query(ExperimentTrial).filter(
        ExperimentTrial.experiment_id == experiment_id
    ).order_by(ExperimentTrial.trial_number.desc()).first()
    return (max_trial.trial_number + 1) if max_trial else 1
```

### **4. Tool & Hardware Rules**
```python
# Tool has one owner organization but can be loaned
def get_tool_owner(tool_id: UUID) -> Organization:
    tool = db.query(Entity).filter(
        Entity.id == tool_id,
        Entity.entity_type == 'device.bioreactor'
    ).first()
    return tool.organization

# Hardware components have unique IDs per controller
def validate_hardware_uniqueness(controller_id: UUID, unique_id: UUID) -> bool:
    existing = db.query(HardwareComponent).filter(
        HardwareComponent.controller_id == controller_id,
        HardwareComponent.unique_id == unique_id
    ).first()
    return existing is None
```

## 🎯 Mental Model Summary

### **Hierarchical Flow**
1. **Organizations** contain **Users** (many-to-many with roles)
2. **Projects** belong to **Organizations** (one primary, many collaborators)
3. **Processes** are templates that can be shared across **Organizations**
4. **Experiments** belong to **Projects** and use **Processes**
5. **Trials** are unique executions of **Experiments**
6. **Tools** (Bioreactors) are owned by **Organizations** but can be shared
7. **Sensors/Actuators** are unique hardware components on **Tool Controllers**

### **Key Principles**
- **Single Source of Truth**: Each entity has one primary owner/container
- **Flexible Sharing**: Resources can be shared across organizational boundaries
- **Unique Identifiers**: Physical hardware components have unique IDs
- **Template Reusability**: Processes can be templates shared across organizations
- **Execution Tracking**: Experiments and trials provide execution history
- **Multi-Tenant Support**: Organizations provide data isolation and access control

## 📊 Entity Relationship Assertions

### **User & Organization Relationships**
1. Users are members of Organizations (many-to-many)
2. An Organization has 1 to many administrators
3. An Organization has 1 to many member users
4. A user can be a member and an administrator of more than one Organization
5. A user must be a member in at least one Organization

### **Project & Organization Relationships**
6. A Project has one primary Organization
7. A Project can have additional associated Organizations
8. Only the primary Organization can delete or archive the project

### **Process Relationships**
9. A Process is a procedural template with loops, explanation of discrete actions and steps
10. A Process can be included in many Experiments or Projects; it need not be unique
11. A Process can be "published" for availability in Process libraries of specific other Organizations
12. A Process can include steps that use one or more Tools (Bioreactors)
13. A Process step can be saved as a template
14. A Process need not be saved as a template, because it is a process and not an Experiment or Experiment Trial

### **Experiment & Trial Relationships**
15. An Experiment Trial is the record of running a set of Processes to achieve some outcome
16. An Experiment can have 1..many Trials of the same Process set
17. An instance of an Experiment can exist only once, and a Trial of an Experiment can exist only once
18. An Experiment exists inside one and only one Project

### **Tool & Hardware Relationships**
19. A Tool can have a type (bioreactor to start)
20. A Tool is the combination of Tool Controller and Tool Vessel
21. A Tool Controller can have 0 to many sensors and 0 to many actuators associated to it
22. A Sensor or Actuator on a Tool Controller should be unique
23. If the physical instance of the sensor or actuator is changed, that is a new Tool Controller-to-Sensor UUID
24. New records from the Tool Controller should reflect that new UUID
25. A Tool is owned by one Organization
26. A Tool can be loaned to other Organizations
27. A Tool can be shared by many Experiments and Projects

This architecture provides a clear mental model for working with the platform while maintaining flexibility for future expansion and complex organizational relationships.
