# Arquitectura del Sistema

## Diagrama de Flujo de Procesamiento

```mermaid
flowchart TD
    Start([Inicio Proceso Diario]) --> GetData[Obtener Facturas API SIESA]
    
    GetData --> FilterRules{Aplicar Reglas<br/>de Negocio}
    
    FilterRules -->|Filtrar| CheckType{Tipo de<br/>Inventario}
    CheckType -->|Excluido| Reject1[Rechazar Factura]
    CheckType -->|Permitido| CheckAmount{Monto Mínimo<br/>$498,000}
    
    CheckAmount -->|Menor| Reject2[Rechazar Factura]
    CheckAmount -->|Mayor/Igual| CheckPrefix{Prefijo}
    
    CheckPrefix -->|'N'| NotasCredito[Notas Crédito]
    CheckPrefix -->|Otro| FacturasValidas[Facturas Válidas]
    
    NotasCredito --> RegisterNC[Registrar en BD SQLite]
    RegisterNC --> SearchPending[Buscar Notas Pendientes]
    
    SearchPending --> TryApply{Intentar Aplicar<br/>a Facturas}
    TryApply -->|Cliente+Producto Match| ValidateAmount{Validar<br/>Montos}
    TryApply -->|No Match| KeepPending[Mantener Pendiente]
    
    ValidateAmount -->|OK| ApplyNC[Aplicar Nota]
    ValidateAmount -->|Excede| KeepPending
    
    ApplyNC --> UpdateDB[Actualizar BD]
    UpdateDB --> Transform[Transformar para Excel]
    
    FacturasValidas --> Transform
    KeepPending --> Transform
    
    Transform --> GenerateExcel[Generar Excel]
    
    Reject1 --> ReportReject[Reporte de Rechazos]
    Reject2 --> ReportReject
    
    GenerateExcel --> GenerateReports[Generar Reportes]
    ReportReject --> GenerateReports
    
    GenerateReports --> SendEmail[Enviar Correo]
    
    SendEmail --> End([Fin Proceso])
    
    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#4CAF50,stroke:#2E7D32,color:#fff
    style FilterRules fill:#2196F3,stroke:#1565C0,color:#fff
    style NotasCredito fill:#FF9800,stroke:#E65100,color:#fff
    style FacturasValidas fill:#4CAF50,stroke:#2E7D32,color:#fff
    style Reject1 fill:#f44336,stroke:#c62828,color:#fff
    style Reject2 fill:#f44336,stroke:#c62828,color:#fff
    style ApplyNC fill:#9C27B0,stroke:#6A1B9A,color:#fff
```

## Diagrama de Componentes

```mermaid
graph TB
    subgraph "GitHub Actions"
        GH[daily_report.yml]
    end
    
    subgraph "Proceso Principal"
        Main[main.py]
    end
    
    subgraph "Módulos de Negocio"
        API[api_client.py<br/>Conexión SIESA]
        BR[business_rules.py<br/>Validaciones]
        NC[notas_credito_manager.py<br/>Gestión NC]
        Excel[excel_processor.py<br/>Generación Excel]
        Email[email_sender.py<br/>Envío Correos]
    end
    
    subgraph "Persistencia"
        DB[(SQLite<br/>notas_credito.db)]
    end
    
    subgraph "Salidas"
        ExcelOut[Excel Facturas]
        TxtReject[Reporte Rechazos]
        TxtNC[Reporte Notas]
    end
    
    GH -->|Ejecuta| Main
    Main --> API
    Main --> BR
    Main --> NC
    Main --> Excel
    Main --> Email
    
    API -->|Facturas Raw| BR
    BR -->|Filtradas| NC
    BR -->|Válidas| Excel
    NC <-->|R/W| DB
    NC -->|Aplicaciones| Excel
    
    Excel --> ExcelOut
    BR --> TxtReject
    NC --> TxtNC
    
    Email -->|Envía| ExcelOut
    
    style Main fill:#2196F3,stroke:#1565C0,color:#fff
    style DB fill:#FF9800,stroke:#E65100,color:#fff
    style GH fill:#4CAF50,stroke:#2E7D32,color:#fff
```

## Diagrama de Base de Datos

```mermaid
erDiagram
    NOTAS_CREDITO ||--o{ APLICACIONES_NOTAS : "tiene"
    
    NOTAS_CREDITO {
        int id PK
        text numero_nota UK
        date fecha_nota
        text nit_cliente
        text nombre_cliente
        text codigo_producto
        text nombre_producto
        real valor_total
        real cantidad
        real saldo_pendiente
        real cantidad_pendiente
        text estado
        timestamp fecha_registro
        timestamp fecha_aplicacion_completa
    }
    
    APLICACIONES_NOTAS {
        int id PK
        int id_nota FK
        text numero_nota
        text numero_factura
        date fecha_factura
        text nit_cliente
        text codigo_producto
        real valor_aplicado
        real cantidad_aplicada
        timestamp fecha_aplicacion
    }
```

## Flujo de Notas Crédito

```mermaid
stateDiagram-v2
    [*] --> Registrada: Nueva NC detectada
    
    Registrada --> Pendiente: Guardar en BD
    
    Pendiente --> Buscando: Proceso diario
    
    Buscando --> Pendiente: No hay facturas<br/>compatibles
    
    Buscando --> Validando: Factura encontrada<br/>(cliente+producto match)
    
    Validando --> Pendiente: Monto/Cantidad<br/>excede límites
    
    Validando --> AplicandoParcial: Aplicar monto<br/>parcial
    
    Validando --> AplicandoCompleta: Aplicar monto<br/>completo
    
    AplicandoParcial --> Pendiente: Queda saldo
    
    AplicandoCompleta --> Aplicada: Saldo = 0
    
    Aplicada --> [*]
    
    note right of Pendiente
        Estado: PENDIENTE
        Se reintenta en
        próximas ejecuciones
    end note
    
    note right of Aplicada
        Estado: APLICADA
        Historial completo
        en aplicaciones_notas
    end note
```

## Reglas de Negocio - Decisión

```mermaid
graph TD
    Factura{Nueva Factura} --> Prefijo{Prefijo<br/>empieza con 'N'?}
    
    Prefijo -->|Sí| NC[Es Nota Crédito]
    Prefijo -->|No| TipoInv{Tipo Inventario<br/>en lista excluidos?}
    
    TipoInv -->|Sí| Rechazar1[RECHAZAR:<br/>Tipo Excluido]
    TipoInv -->|No| Monto{Monto >=<br/>$498,000?}
    
    Monto -->|No| Rechazar2[RECHAZAR:<br/>Monto Bajo]
    Monto -->|Sí| Aceptar[ACEPTAR:<br/>Factura Válida]
    
    NC --> GuardarNC[Guardar en BD]
    GuardarNC --> BuscarMatch[Buscar Facturas<br/>Compatible]
    
    BuscarMatch --> Match{Cliente +<br/>Producto Match?}
    Match -->|No| Pendiente[Queda PENDIENTE]
    Match -->|Sí| ValidarMonto{Monto NC <=<br/>Monto Factura?}
    
    ValidarMonto -->|No| Pendiente
    ValidarMonto -->|Sí| Aplicar[APLICAR a Factura]
    
    Aplicar --> ActualizarBD[Actualizar Saldos BD]
    
    style Rechazar1 fill:#f44336,stroke:#c62828,color:#fff
    style Rechazar2 fill:#f44336,stroke:#c62828,color:#fff
    style Aceptar fill:#4CAF50,stroke:#2E7D32,color:#fff
    style Aplicar fill:#9C27B0,stroke:#6A1B9A,color:#fff
    style Pendiente fill:#FF9800,stroke:#E65100,color:#fff
```

## Secuencia de Aplicación de Nota Crédito

```mermaid
sequenceDiagram
    participant Main as main.py
    participant NC as NotasCreditoManager
    participant DB as SQLite DB
    participant Factura as Factura Válida
    
    Main->>NC: Registrar nota crédito
    NC->>DB: INSERT nota
    DB-->>NC: ID nota
    
    Main->>NC: Procesar facturas
    
    loop Para cada factura
        NC->>DB: Buscar notas pendientes<br/>(cliente + producto)
        DB-->>NC: Lista de notas
        
        alt Hay notas compatibles
            NC->>NC: Validar montos
            
            alt Monto válido
                NC->>DB: INSERT aplicación
                NC->>DB: UPDATE saldo nota
                NC-->>Factura: Nota aplicada
                
                alt Saldo = 0
                    NC->>DB: UPDATE estado='APLICADA'
                end
            end
        end
    end
    
    NC-->>Main: Lista aplicaciones realizadas
```

---

## Visualización de Archivos

Para ver estos diagramas:
1. Visualizador en GitHub (automático al ver este archivo)
2. VS Code con extensión "Markdown Preview Mermaid Support"
3. Sitio web: https://mermaid.live/

---

*Diagramas generados con Mermaid*
*Compatible con GitHub, GitLab, Notion, Confluence, etc.*
