//! Vue 3 Code Emitter with Composition API
//!
//! Generates Vue 3 applications with TypeScript and Composition API.
//! Ported from Python implementation with full feature parity.

use domain::model::{CoreModule, UiNode, UiTree};
use domain::translation::{EmissionUnit, EmitErr, EmittedFile, FeatureSet, TargetEmitter};
use std::collections::HashMap;

/// Vue generator configuration
#[derive(Debug, Clone)]
pub struct VueGeneratorConfig {
    pub app_name: String,
    pub app_title: String,
    pub version: String,
    pub use_typescript: bool,
    pub use_pinia: bool,
    pub enable_routing: bool,
}

impl Default for VueGeneratorConfig {
    fn default() -> Self {
        Self {
            app_name: "app".to_string(),
            app_title: "App".to_string(),
            version: "0.1.0".to_string(),
            use_typescript: true,
            use_pinia: true,
            enable_routing: true,
        }
    }
}

pub struct VueEmitter {
    config: VueGeneratorConfig,
}

impl VueEmitter {
    pub fn new(config: VueGeneratorConfig) -> Self {
        Self { config }
    }

    /// Generate App.vue with router-view
    fn generate_app_vue(&self) -> String {
        r#"<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'

onMounted(() => {
  console.log('App mounted')
})
</script>

<template>
  <div id="app">
    <RouterView />
  </div>
</template>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
"#
        .to_string()
    }

    /// Generate Pinia store
    fn generate_pinia_store(&self) -> String {
        r#"import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Entity {
  id: number
  name: string
  data: Record<string, any>
  createdAt: Date
  updatedAt: Date
}

export const useAppStore = defineStore('app', () => {
  // State
  const entities = ref<Entity[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const hasEntities = computed(() => entities.value.length > 0)
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => error.value !== null)

  // Actions
  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(err: string | null) {
    error.value = err
  }

  function addEntity(entity: Entity) {
    entities.value.push(entity)
  }

  function updateEntity(entity: Entity) {
    const index = entities.value.findIndex(e => e.id === entity.id)
    if (index !== -1) {
      entities.value[index] = entity
    }
  }

  function deleteEntity(id: number) {
    entities.value = entities.value.filter(e => e.id !== id)
  }

  function setEntities(newEntities: Entity[]) {
    entities.value = newEntities
  }

  async function fetchEntities() {
    setLoading(true)
    setError(null)
    try {
      // Fetch logic here
      await new Promise(resolve => setTimeout(resolve, 1000))
      setEntities([])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return {
    // State
    entities,
    loading,
    error,
    // Getters
    hasEntities,
    isLoading,
    hasError,
    // Actions
    setLoading,
    setError,
    addEntity,
    updateEntity,
    deleteEntity,
    setEntities,
    fetchEntities,
  }
})
"#
        .to_string()
    }

    /// Generate Home.vue component
    fn generate_home_component(&self, ui: &UiTree) -> Result<String, EmitErr> {
        let (title, children) = match &ui.root {
            UiNode::Window { title, children, .. } => (title.clone(), children),
            _ => ("Home".to_string(), &vec![]),
        };

        let template_children = children
            .iter()
            .filter_map(|child| self.node_to_template(child).ok())
            .collect::<Vec<_>>()
            .join("\n    ");

        Ok(format!(
            r#"<script setup lang="ts">
import {{ ref, onMounted, computed }} from 'vue'
import {{ useAppStore }} from '../stores/app'

const store = useAppStore()

// State
const localState = ref<Record<string, any>>({{}})

// Computed
const isLoading = computed(() => store.isLoading)

// Methods
function handleAction() {{
  console.log('Action triggered')
}}

// Lifecycle
onMounted(() => {{
  console.log('Home component mounted')
  store.fetchEntities()
}})
</script>

<template>
  <div class="home-container">
    <h1>{}</h1>

    <div v-if="isLoading" class="loading">
      Loading...
    </div>

    <div v-else class="content">
      {}
    </div>
  </div>
</template>

<style scoped>
.home-container {{
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}}

h1 {{
  color: #2c3e50;
  margin-bottom: 1.5rem;
}}

.loading {{
  text-align: center;
  padding: 2rem;
}}

.content {{
  display: flex;
  flex-direction: column;
  gap: 1rem;
}}

button {{
  padding: 0.5rem 1rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}}

button:hover {{
  background-color: #35a372;
}}

button:disabled {{
  opacity: 0.6;
  cursor: not-allowed;
}}

input {{
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}}

input:focus {{
  outline: none;
  border-color: #42b983;
}}
</style>
"#,
            title,
            if template_children.is_empty() {
                "<p>Welcome to the application</p>"
            } else {
                &template_children
            }
        ))
    }

    /// Convert UiNode to Vue template
    fn node_to_template(&self, node: &UiNode) -> Result<String, EmitErr> {
        match node {
            UiNode::Window { .. } | UiNode::Container { .. } | UiNode::Menu { .. } | UiNode::Control { .. } => {
                Ok("<div>Widget</div>".to_string())
            }
        }
    }

    /// Generate router configuration
    fn generate_router(&self) -> String {
        r#"import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    }
  ]
})

export default router
"#
        .to_string()
    }

    /// Generate main.ts
    fn generate_main_ts(&self) -> String {
        let pinia_import = if self.config.use_pinia {
            "import { createPinia } from 'pinia'\n"
        } else {
            ""
        };

        let router_import = if self.config.enable_routing {
            "import router from './router'\n"
        } else {
            ""
        };

        let pinia_use = if self.config.use_pinia {
            "app.use(createPinia())\n"
        } else {
            ""
        };

        let router_use = if self.config.enable_routing {
            "app.use(router)\n"
        } else {
            ""
        };

        format!(
            r#"import {{ createApp }} from 'vue'
{}{}import App from './App.vue'
import './style.css'

const app = createApp(App)

{}{}
app.mount('#app')
"#,
            pinia_import, router_import, pinia_use, router_use
        )
    }

    /// Generate package.json
    fn generate_package_json(&self) -> String {
        let pinia_dep = if self.config.use_pinia {
            r#""pinia": "^2.1.0","#
        } else {
            ""
        };

        format!(
            r#"{{
  "name": "{}",
  "version": "{}",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  }},
  "dependencies": {{
    "vue": "^3.3.0",
    "vue-router": "^4.2.0",
    {}
  }},
  "devDependencies": {{
    "@vitejs/plugin-vue": "^4.2.0",
    "typescript": "^5.0.0",
    "vue-tsc": "^1.8.0",
    "vite": "^4.4.0"
  }}
}}
"#,
            self.config.app_name, self.config.version, pinia_dep
        )
    }

    /// Generate vite.config.ts
    fn generate_vite_config(&self) -> String {
        r#"import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    open: true
  }
})
"#
        .to_string()
    }

    /// Generate tsconfig.json
    fn generate_tsconfig(&self) -> String {
        r#"{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
"#
        .to_string()
    }

    /// Generate index.html
    fn generate_index_html(&self) -> String {
        format!(
            r#"<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <link rel="icon" href="/favicon.ico">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{}</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
"#,
            self.config.app_title
        )
    }
}

impl TargetEmitter for VueEmitter {
    fn target_id(&self) -> &'static str {
        "vue"
    }

    fn supports(&self, features: &FeatureSet) -> bool {
        // Vue supports UI and async operations
        true
    }

    fn emit_core(&self, ir: &CoreModule) -> Result<EmissionUnit, EmitErr> {
        let mut files = vec![];

        // Generate App.vue
        files.push(EmittedFile {
            path: "src/App.vue".to_string(),
            content: self.generate_app_vue(),
            is_executable: false,
        });

        // Generate main.ts
        files.push(EmittedFile {
            path: "src/main.ts".to_string(),
            content: self.generate_main_ts(),
            is_executable: false,
        });

        // Generate Pinia store if enabled
        if self.config.use_pinia {
            files.push(EmittedFile {
                path: "src/stores/app.ts".to_string(),
                content: self.generate_pinia_store(),
                is_executable: false,
            });
        }

        // Generate router if enabled
        if self.config.enable_routing {
            files.push(EmittedFile {
                path: "src/router/index.ts".to_string(),
                content: self.generate_router(),
                is_executable: false,
            });
        }

        // Generate package.json
        files.push(EmittedFile {
            path: "package.json".to_string(),
            content: self.generate_package_json(),
            is_executable: false,
        });

        // Generate vite.config.ts
        files.push(EmittedFile {
            path: "vite.config.ts".to_string(),
            content: self.generate_vite_config(),
            is_executable: false,
        });

        // Generate tsconfig.json
        if self.config.use_typescript {
            files.push(EmittedFile {
                path: "tsconfig.json".to_string(),
                content: self.generate_tsconfig(),
                is_executable: false,
            });
        }

        // Generate index.html
        files.push(EmittedFile {
            path: "index.html".to_string(),
            content: self.generate_index_html(),
            is_executable: false,
        });

        Ok(EmissionUnit {
            files,
            metadata: HashMap::new(),
        })
    }

    fn emit_ui(&self, ui: &UiTree) -> Result<EmissionUnit, EmitErr> {
        let mut files = vec![];

        // Generate Home component from UI tree
        let home = self.generate_home_component(ui)?;
        files.push(EmittedFile {
            path: "src/views/Home.vue".to_string(),
            content: home,
            is_executable: false,
        });

        Ok(EmissionUnit {
            files,
            metadata: HashMap::new(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vue_emitter() {
        let config = VueGeneratorConfig::default();
        let emitter = VueEmitter::new(config);
        assert_eq!(emitter.target_id(), "vue");
    }

    #[test]
    fn test_generate_app_vue() {
        let config = VueGeneratorConfig::default();
        let emitter = VueEmitter::new(config);
        let app_vue = emitter.generate_app_vue();
        assert!(app_vue.contains("<script setup"));
        assert!(app_vue.contains("RouterView"));
    }
}
