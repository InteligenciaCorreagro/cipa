#!/bin/bash

# Script de Migración: De Artifacts a Persistencia en Repositorio
# Versión 3.0 - Corrección de Pérdida de Datos

set -e  # Salir si hay errores

echo "================================================================"
echo "  MIGRACIÓN: Sistema de Persistencia de Base de Datos"
echo "  De: Artifacts (no funciona) → A: Git Commits (funciona)"
echo "================================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo "ℹ️  $1"
}

# ============================================================
# 1. VERIFICACIONES PREVIAS
# ============================================================
echo "PASO 1: Verificaciones Previas"
echo "------------------------------"

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    print_error "No se encontró main.py. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi
print_success "Directorio del proyecto verificado"

# Verificar que Git está configurado
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Este no es un repositorio Git. Ejecuta 'git init' primero."
    exit 1
fi
print_success "Repositorio Git detectado"

# Verificar que no hay cambios sin commit
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    print_warning "Hay cambios sin commit en tu repositorio"
    echo "Recomendamos hacer commit o stash antes de continuar."
    read -p "¿Continuar de todos modos? (s/N): " respuesta
    if [[ ! "$respuesta" =~ ^[sS]$ ]]; then
        echo "Migración cancelada."
        exit 0
    fi
fi

echo ""

# ============================================================
# 2. BACKUP DE ARCHIVOS ACTUALES
# ============================================================
echo "PASO 2: Crear Backups de Seguridad"
echo "-----------------------------------"

BACKUP_DIR="migration_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup de workflow si existe
if [ -f ".github/workflows/daily_process.yml" ]; then
    cp .github/workflows/daily_process.yml "$BACKUP_DIR/"
    print_success "Backup de workflow creado"
fi

# Backup de .gitignore si existe
if [ -f ".gitignore" ]; then
    cp .gitignore "$BACKUP_DIR/"
    print_success "Backup de .gitignore creado"
fi

# Backup de base de datos si existe
if [ -f "data/notas_credito.db" ]; then
    mkdir -p "$BACKUP_DIR/data"
    cp data/notas_credito.db "$BACKUP_DIR/data/"
    SIZE=$(ls -lh data/notas_credito.db | awk '{print $5}')
    print_success "Backup de base de datos creado (Tamaño: $SIZE)"
    
    # Mostrar estadísticas actuales
    echo ""
    print_info "Estadísticas de la BD actual:"
    sqlite3 data/notas_credito.db "SELECT '  Notas crédito: ' || COUNT(*) FROM notas_credito;" 2>/dev/null || echo "  Error al leer BD"
    sqlite3 data/notas_credito.db "SELECT '  Aplicaciones: ' || COUNT(*) FROM aplicaciones_notas;" 2>/dev/null || echo "  Error al leer BD"
    echo ""
fi

print_success "Backups guardados en: $BACKUP_DIR/"
echo ""

# ============================================================
# 3. ACTUALIZAR .gitignore
# ============================================================
echo "PASO 3: Actualizar .gitignore"
echo "------------------------------"

if [ -f ".gitignore.new" ]; then
    cp .gitignore.new .gitignore
    print_success ".gitignore actualizado (la BD ya NO se ignora)"
else
    print_warning ".gitignore.new no encontrado, actualizando manualmente..."
    
    # Crear nuevo .gitignore
    cat > .gitignore << 'EOF'
.env

# Python
__pycache__/
*.py[cod]
*.class
*.so
.Python
env/
venv/
ENV/

# Output files (temporales)
output/
*.xlsx
!templates/plantilla.xlsx

# IMPORTANTE: NO IGNORAR LA BASE DE DATOS
# La base de datos DEBE estar en el repositorio
# data/  <- COMENTADO
# *.db   <- COMENTADO

# Solo ignorar backups temporales
data/*.backup
data/*.db.backup
backups/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
EOF
    print_success ".gitignore creado con configuración correcta"
fi

echo ""

# ============================================================
# 4. ACTUALIZAR WORKFLOW
# ============================================================
echo "PASO 4: Actualizar Workflow de GitHub Actions"
echo "----------------------------------------------"

mkdir -p .github/workflows

if [ -f "daily_process.yml.new" ]; then
    cp daily_process.yml.new .github/workflows/daily_process.yml
    print_success "Workflow actualizado con persistencia en repositorio"
else
    print_error "daily_process.yml.new no encontrado"
    echo "Por favor descarga el archivo del repositorio y colócalo como:"
    echo "  .github/workflows/daily_process.yml"
    exit 1
fi

echo ""

# ============================================================
# 5. CREAR COMMIT INICIAL
# ============================================================
echo "PASO 5: Crear Commit con la Base de Datos"
echo "------------------------------------------"

# Agregar archivos al staging
git add .gitignore
git add .github/workflows/daily_process.yml

# Agregar BD si existe
if [ -f "data/notas_credito.db" ]; then
    git add data/notas_credito.db
    print_success "Base de datos agregada al commit"
    
    # Mostrar tamaño
    SIZE=$(ls -lh data/notas_credito.db | awk '{print $5}')
    print_info "Tamaño de la BD: $SIZE"
else
    print_warning "No se encontró base de datos existente"
    print_info "Se creará en la primera ejecución del workflow"
fi

# Verificar si hay cambios para commit
if git diff --staged --quiet; then
    print_info "No hay cambios para hacer commit"
else
    # Crear commit
    COMMIT_MSG="🔧 FIX CRÍTICO: Persistir BD en repositorio

Problema solucionado:
- Artifacts no persisten entre ejecuciones → pérdida de datos
- Cada día se creaba BD nueva → notas desaparecían

Solución:
- BD ahora se guarda directamente en el repositorio
- Commits automáticos después de cada ejecución
- Historial completo en Git para auditoría

Cambios:
- Workflow actualizado con git commits
- .gitignore actualizado (no ignora *.db)
- Permisos agregados (contents: write)

Fecha: $(date '+%Y-%m-%d %H:%M:%S')
"
    
    git commit -m "$COMMIT_MSG"
    print_success "Commit creado exitosamente"
fi

echo ""

# ============================================================
# 6. PUSH AL REPOSITORIO
# ============================================================
echo "PASO 6: Enviar Cambios al Repositorio Remoto"
echo "---------------------------------------------"

read -p "¿Deseas hacer push al repositorio remoto ahora? (S/n): " respuesta
if [[ ! "$respuesta" =~ ^[nN]$ ]]; then
    if git push; then
        print_success "Cambios enviados al repositorio remoto"
    else
        print_error "Error al hacer push. Hazlo manualmente con: git push"
    fi
else
    print_warning "Recuerda hacer push manualmente con: git push"
fi

echo ""

# ============================================================
# 7. VERIFICACIONES FINALES
# ============================================================
echo "PASO 7: Verificaciones Finales"
echo "-------------------------------"

# Verificar .gitignore
if grep -q "^data/$\|^*.db$" .gitignore; then
    print_error ".gitignore todavía ignora la BD"
    print_info "Verifica manualmente que data/ y *.db NO estén en .gitignore"
else
    print_success ".gitignore correcto (no ignora la BD)"
fi

# Verificar que la BD está trackeada
if [ -f "data/notas_credito.db" ]; then
    if git ls-files --error-unmatch data/notas_credito.db > /dev/null 2>&1; then
        print_success "Base de datos está siendo trackeada por Git"
    else
        print_warning "Base de datos NO está siendo trackeada"
        print_info "Ejecuta: git add data/notas_credito.db"
    fi
fi

# Verificar workflow
if [ -f ".github/workflows/daily_process.yml" ]; then
    if grep -q "permissions:" .github/workflows/daily_process.yml; then
        print_success "Workflow tiene configuración de permisos"
    else
        print_error "Workflow no tiene configuración de permisos"
        print_info "Agrega manualmente la sección 'permissions: contents: write'"
    fi
fi

echo ""

# ============================================================
# 8. RESUMEN Y PRÓXIMOS PASOS
# ============================================================
echo "================================================================"
echo "  ✅ MIGRACIÓN COMPLETADA"
echo "================================================================"
echo ""
echo "📋 Resumen de cambios:"
echo "  - Workflow actualizado: .github/workflows/daily_process.yml"
echo "  - .gitignore actualizado (BD ya NO se ignora)"
if [ -f "data/notas_credito.db" ]; then
    echo "  - Base de datos incluida en el commit"
fi
echo "  - Backups guardados en: $BACKUP_DIR/"
echo ""
echo "🚀 Próximos pasos:"
echo ""
echo "1. HACER PUSH (si no lo hiciste):"
echo "   git push"
echo ""
echo "2. VERIFICAR EN GITHUB:"
echo "   - Ve a tu repositorio"
echo "   - Navega a data/notas_credito.db"
echo "   - Deberías poder verlo"
echo ""
echo "3. EJECUTAR WORKFLOW MANUALMENTE:"
echo "   - GitHub → Actions → Proceso Completo Diario"
echo "   - Run workflow"
echo ""
echo "4. VERIFICAR LOGS:"
echo "   - Buscar: '✅ Base de datos encontrada en el repositorio'"
echo "   - Buscar: '✅ Base de datos actualizada y persistida'"
echo ""
echo "5. MONITOREAR 2-3 DÍAS:"
echo "   - Verificar que las notas NO desaparezcan"
echo "   - Ver commits automáticos: git log -- data/notas_credito.db"
echo ""
echo "================================================================"
echo ""
echo "📞 Si encuentras problemas:"
echo "   - Revisa CORRECCION_PERSISTENCIA_BD.md"
echo "   - Verifica permisos del workflow (contents: write)"
echo "   - Restaura desde backup si es necesario: $BACKUP_DIR/"
echo ""
echo "================================================================"

# Crear archivo de estado
cat > migration_status.txt << EOF
Migración completada: $(date '+%Y-%m-%d %H:%M:%S')

Backups en: $BACKUP_DIR/

Estado:
- Workflow: ✅ Actualizado
- .gitignore: ✅ Actualizado
- BD en repo: $([ -f "data/notas_credito.db" ] && echo "✅ Sí" || echo "⚠️  Se creará en primera ejecución")

Próximos pasos:
1. git push (si no se hizo)
2. Ejecutar workflow manualmente
3. Verificar logs
4. Monitorear 2-3 días

Para rollback:
cp $BACKUP_DIR/.github/workflows/daily_process.yml .github/workflows/
cp $BACKUP_DIR/.gitignore .gitignore
git add -A
git commit -m "Rollback de migración"
git push
EOF

print_success "Estado de migración guardado en: migration_status.txt"
echo ""
