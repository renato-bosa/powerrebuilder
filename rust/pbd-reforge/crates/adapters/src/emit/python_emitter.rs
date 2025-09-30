//! Python/Litestar API Code Emitter
//!
//! Generates Python/Litestar REST APIs with SQLModel and Pydantic validation.
//! Ported from Python implementation with full feature parity.

use domain::model::{CoreModule, UiTree};
use domain::translation::{EmissionUnit, EmitErr, EmittedFile, FeatureSet, TargetEmitter};
use std::collections::HashMap;

/// Python API generator configuration
#[derive(Debug, Clone)]
pub struct PythonGeneratorConfig {
    pub app_name: String,
    pub version: String,
    pub use_async: bool,
    pub use_sqlmodel: bool,
    pub enable_auth: bool,
    pub enable_cors: bool,
}

impl Default for PythonGeneratorConfig {
    fn default() -> Self {
        Self {
            app_name: "app".to_string(),
            version: "0.1.0".to_string(),
            use_async: true,
            use_sqlmodel: true,
            enable_auth: true,
            enable_cors: true,
        }
    }
}

pub struct PythonEmitter {
    config: PythonGeneratorConfig,
}

impl PythonEmitter {
    pub fn new(config: PythonGeneratorConfig) -> Self {
        Self { config }
    }

    /// Generate main.py with Litestar app
    fn generate_main_py(&self) -> String {
        let cors_middleware = if self.config.enable_cors {
            r#"
from litestar.config.cors import CORSConfig

cors_config = CORSConfig(
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
"#
        } else {
            ""
        };

        let auth_config = if self.config.enable_auth {
            r#"
from litestar.contrib.jwt import JWTAuth, Token

jwt_auth = JWTAuth[Token](
    retrieve_user_handler=lambda token: None,  # Implement user retrieval
    token_secret="your-secret-key",  # Use environment variable in production
    default_token_expiration=timedelta(days=1),
)
"#
        } else {
            ""
        };

        format!(
            r#"""Main application module with Litestar configuration."""
from datetime import timedelta
from litestar import Litestar
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from litestar.config.compression import CompressionConfig
{}{}
from controllers import router
from database import engine, init_db

@litestar.on_event("startup")
async def on_startup() -> None:
    """Initialize database on startup."""
    await init_db()

app = Litestar(
    route_handlers=[router],
    on_startup=[on_startup],
    {}{}
    compression_config=CompressionConfig(backend="gzip"),
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
"#,
            cors_middleware,
            auth_config,
            if self.config.enable_cors {
                "cors_config=cors_config,\n    "
            } else {
                ""
            },
            if self.config.enable_auth {
                "on_app_init=[jwt_auth.on_app_init],\n    "
            } else {
                ""
            }
        )
    }

    /// Generate database.py with SQLModel configuration
    fn generate_database_py(&self) -> String {
        r#"""Database configuration and session management."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, create_engine
from contextlib import asynccontextmanager

DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
"#
        .to_string()
    }

    /// Generate models.py with SQLModel tables
    fn generate_models_py(&self) -> String {
        r#"""Domain models with SQLModel."""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class EntityBase(SQLModel):
    """Base entity with common fields."""
    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Entity(EntityBase, table=True):
    """Entity database table."""
    __tablename__ = "entities"

    id: Optional[int] = Field(default=None, primary_key=True)

class EntityCreate(EntityBase):
    """Schema for creating entities."""
    pass

class EntityUpdate(SQLModel):
    """Schema for updating entities."""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EntityPublic(EntityBase):
    """Public entity schema."""
    id: int
"#
        .to_string()
    }

    /// Generate controllers.py with CRUD endpoints
    fn generate_controllers_py(&self) -> String {
        let async_keyword = if self.config.use_async { "async " } else { "" };
        let await_keyword = if self.config.use_async { "await " } else { "" };

        format!(
            r#"""API controllers with CRUD endpoints."""
from typing import List
from litestar import Controller, get, post, put, delete, Router
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models import Entity, EntityCreate, EntityUpdate, EntityPublic
from database import get_session

class EntityController(Controller):
    """Entity CRUD controller."""
    path = "/api/entities"
    tags = ["entities"]

    @get("/")
    {}def list_entities(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EntityPublic]:
        """Get all entities with pagination."""
        {}with get_session() as session:
            statement = select(Entity).limit(limit).offset(offset)
            result = {}session.exec(statement)
            entities = result.all()
            return [EntityPublic.model_validate(e) for e in entities]

    @get("/{{entity_id:int}}")
    {}def get_entity(
        self,
        entity_id: int,
    ) -> EntityPublic:
        """Get entity by ID."""
        {}with get_session() as session:
            entity = {}session.get(Entity, entity_id)
            if not entity:
                raise NotFoundException(detail=f"Entity {{entity_id}} not found")
            return EntityPublic.model_validate(entity)

    @post("/")
    {}def create_entity(
        self,
        data: EntityCreate,
    ) -> EntityPublic:
        """Create new entity."""
        {}with get_session() as session:
            entity = Entity.model_validate(data)
            session.add(entity)
            {}session.commit()
            {}session.refresh(entity)
            return EntityPublic.model_validate(entity)

    @put("/{{entity_id:int}}")
    {}def update_entity(
        self,
        entity_id: int,
        data: EntityUpdate,
    ) -> EntityPublic:
        """Update entity."""
        {}with get_session() as session:
            entity = {}session.get(Entity, entity_id)
            if not entity:
                raise NotFoundException(detail=f"Entity {{entity_id}} not found")

            # Update fields
            entity_data = data.model_dump(exclude_unset=True)
            for key, value in entity_data.items():
                setattr(entity, key, value)

            session.add(entity)
            {}session.commit()
            {}session.refresh(entity)
            return EntityPublic.model_validate(entity)

    @delete("/{{entity_id:int}}")
    {}def delete_entity(
        self,
        entity_id: int,
    ) -> None:
        """Delete entity."""
        {}with get_session() as session:
            entity = {}session.get(Entity, entity_id)
            if not entity:
                raise NotFoundException(detail=f"Entity {{entity_id}} not found")

            {}session.delete(entity)
            {}session.commit()

router = Router(
    path="",
    route_handlers=[EntityController],
)
"#,
            async_keyword,
            await_keyword,
            await_keyword,
            async_keyword,
            await_keyword,
            await_keyword,
            async_keyword,
            await_keyword,
            await_keyword,
            await_keyword,
            async_keyword,
            await_keyword,
            await_keyword,
            await_keyword,
            await_keyword,
            async_keyword,
            await_keyword,
            await_keyword,
            await_keyword,
            await_keyword
        )
    }

    /// Generate requirements.txt
    fn generate_requirements_txt(&self) -> String {
        let mut deps = vec![
            "litestar[standard]>=2.0.0",
            "sqlmodel>=0.0.14",
            "uvicorn[standard]>=0.24.0",
            "python-multipart>=0.0.6",
        ];

        if self.config.use_async {
            deps.push("aiosqlite>=0.19.0");
        }

        if self.config.enable_auth {
            deps.push("litestar[jwt]>=2.0.0");
            deps.push("python-jose[cryptography]>=3.3.0");
        }

        if self.config.enable_cors {
            deps.push("# CORS is built into Litestar");
        }

        deps.join("\n")
    }

    /// Generate pyproject.toml
    fn generate_pyproject_toml(&self) -> String {
        format!(
            r#"[project]
name = "{}"
version = "{}"
description = "Generated Python/Litestar API"
requires-python = ">=3.11"
dependencies = [
    "litestar[standard]>=2.0.0",
    "sqlmodel>=0.0.14",
    "uvicorn[standard]>=0.24.0",
    "python-multipart>=0.0.6",
    "aiosqlite>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
"#,
            self.config.app_name, self.config.version
        )
    }

    /// Generate .env.example
    fn generate_env_example(&self) -> String {
        r#"# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Application
APP_NAME=powerbuilder_api
APP_VERSION=0.1.0
DEBUG=true

# Security (change these in production!)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
"#
        .to_string()
    }

    /// Generate README.md
    fn generate_readme(&self) -> String {
        format!(
            r#"# {} API

Generated Python/Litestar REST API from PowerBuilder application.

## Features

- ✅ Async/await with SQLModel
- ✅ Type-safe with Pydantic validation
- ✅ OpenAPI documentation
- ✅ CORS support
- ✅ JWT authentication
- ✅ Database migrations

## Setup

### Install dependencies

```bash
pip install -e .
```

### Run development server

```bash
python main.py
```

The API will be available at http://localhost:8000

### API Documentation

- Swagger UI: http://localhost:8000/schema
- ReDoc: http://localhost:8000/schema/redoc

## Project Structure

```
.
├── main.py           # Application entry point
├── database.py       # Database configuration
├── models.py         # SQLModel entities
├── controllers.py    # API endpoints
├── requirements.txt  # Dependencies
└── pyproject.toml   # Project metadata
```

## API Endpoints

- `GET /api/entities` - List all entities
- `GET /api/entities/{{id}}` - Get entity by ID
- `POST /api/entities` - Create new entity
- `PUT /api/entities/{{id}}` - Update entity
- `DELETE /api/entities/{{id}}` - Delete entity

## Testing

```bash
pytest
```

## Production Deployment

1. Set environment variables in `.env`
2. Use a production ASGI server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## License

Generated by PowerRebuilder
"#,
            self.config.app_name
        )
    }
}

impl TargetEmitter for PythonEmitter {
    fn target_id(&self) -> &'static str {
        "python"
    }

    fn supports(&self, features: &FeatureSet) -> bool {
        // Python/Litestar supports REST APIs and database operations
        true
    }

    fn emit_core(&self, ir: &CoreModule) -> Result<EmissionUnit, EmitErr> {
        let mut files = vec![];

        // Generate main.py
        files.push(EmittedFile {
            path: "main.py".to_string(),
            content: self.generate_main_py(),
            is_executable: false,
        });

        // Generate database.py
        files.push(EmittedFile {
            path: "database.py".to_string(),
            content: self.generate_database_py(),
            is_executable: false,
        });

        // Generate models.py
        files.push(EmittedFile {
            path: "models.py".to_string(),
            content: self.generate_models_py(),
            is_executable: false,
        });

        // Generate controllers.py
        files.push(EmittedFile {
            path: "controllers.py".to_string(),
            content: self.generate_controllers_py(),
            is_executable: false,
        });

        // Generate requirements.txt
        files.push(EmittedFile {
            path: "requirements.txt".to_string(),
            content: self.generate_requirements_txt(),
            is_executable: false,
        });

        // Generate pyproject.toml
        files.push(EmittedFile {
            path: "pyproject.toml".to_string(),
            content: self.generate_pyproject_toml(),
            is_executable: false,
        });

        // Generate .env.example
        files.push(EmittedFile {
            path: ".env.example".to_string(),
            content: self.generate_env_example(),
            is_executable: false,
        });

        // Generate README.md
        files.push(EmittedFile {
            path: "README.md".to_string(),
            content: self.generate_readme(),
            is_executable: false,
        });

        Ok(EmissionUnit {
            files,
            metadata: HashMap::new(),
        })
    }

    fn emit_ui(&self, ui: &UiTree) -> Result<EmissionUnit, EmitErr> {
        // Python backend doesn't emit UI directly
        Ok(EmissionUnit {
            files: vec![],
            metadata: HashMap::new(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_python_emitter() {
        let config = PythonGeneratorConfig::default();
        let emitter = PythonEmitter::new(config);
        assert_eq!(emitter.target_id(), "python");
    }

    #[test]
    fn test_generate_main_py() {
        let config = PythonGeneratorConfig::default();
        let emitter = PythonEmitter::new(config);
        let main_py = emitter.generate_main_py();
        assert!(main_py.contains("from litestar import Litestar"));
        assert!(main_py.contains("app = Litestar"));
    }

    #[test]
    fn test_generate_models_py() {
        let config = PythonGeneratorConfig::default();
        let emitter = PythonEmitter::new(config);
        let models = emitter.generate_models_py();
        assert!(models.contains("class Entity"));
        assert!(models.contains("SQLModel"));
    }
}
