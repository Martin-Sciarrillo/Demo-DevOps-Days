import { useState } from "react";

const formatMarkdown = (text: string): string => {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br />");
};

interface SourceInfo {
  kb: string;
  title?: string;
  filepath?: string;
  url?: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  sources?: SourceInfo[];
}

type WorkflowStep = "idle" | "routing" | "politicas" | "runbooks" | "herramientas" | "complete";

// Strongly type the node IDs used in the canvas/status logic.
type NodeId =
  | "input"
  | "orchestrator"
  | "politicas"
  | "runbooks"
  | "herramientas"
  | "complete"
  | "idle";

interface TraceLog {
  timestamp: string;
  type: "info" | "route" | "query" | "response";
  message: string;
}

interface AgentInfo {
  id: string;
  name: string;
  icon: string;
  description: string;
  model: string;
  connectedKB: string | null;
  knowledgeSources: string[];
}

interface KBInfo {
  id: string;
  name: string;
  icon: string;
  description: string;
  retrievalMode: string;
  model: string;
  knowledgeSources: string[];
}

const agents: AgentInfo[] = [
  {
    id: "orchestrator",
    name: "Orquestador",
    icon: "",
    description:
      "Analiza la consulta y la deriva al agente especialista correcto: Políticas, Runbooks o Herramientas.",
    model: "gpt-4.1",
    connectedKB: null,
    knowledgeSources: [],
  },
  {
    id: "politicas",
    name: "Agente Políticas",
    icon: "",
    description:
      "Políticas de on-call, rotaciones de guardia, niveles de severidad, SLA/SLO, postmortem y certificaciones.",
    model: "gpt-4o",
    connectedKB: "index-politicas",
    knowledgeSources: ["index-politicas"],
  },
  {
    id: "runbooks",
    name: "Agente Runbooks",
    icon: "",
    description:
      "Runbooks operacionales, playbooks de incidentes P1, procedimientos de respuesta a alertas y troubleshooting.",
    model: "gpt-4o",
    connectedKB: "index-runbooks",
    knowledgeSources: ["index-runbooks"],
  },
  {
    id: "herramientas",
    name: "Agente Herramientas",
    icon: "",
    description:
      "Catálogo de herramientas internas: Kubernetes/EKS, Terraform, Vault, CI/CD, ArgoCD, Grafana, Datadog.",
    model: "gpt-4o",
    connectedKB: "index-herramientas",
    knowledgeSources: ["index-herramientas"],
  },
];

const knowledgeBases: KBInfo[] = [
  {
    id: "index-politicas",
    name: "KB Políticas",
    icon: "",
    description:
      "Políticas de on-call, guardia, escalado, SLA/SLO, postmortem, cultura blameless y certificaciones.",
    retrievalMode: "Semantic Search",
    model: "gpt-4o",
    knowledgeSources: ["index-politicas"],
  },
  {
    id: "index-runbooks",
    name: "KB Runbooks",
    icon: "",
    description:
      "Runbooks operacionales, playbooks de incidentes, procedimientos de respuesta a alertas y troubleshooting.",
    retrievalMode: "Semantic Search",
    model: "gpt-4o",
    knowledgeSources: ["index-runbooks"],
  },
  {
    id: "index-herramientas",
    name: "KB Herramientas",
    icon: "",
    description:
      "Catálogo de herramientas de infraestructura, CI/CD, monitoring, observabilidad y gestión de secretos.",
    retrievalMode: "Semantic Search",
    model: "gpt-4o",
    knowledgeSources: ["index-herramientas"],
  },
];

const sourceLogos: Record<string, string> = {
  "politicas-agent": "📋",
  "runbooks-agent": "📖",
  "herramientas-agent": "🛠️",
  "index-politicas": "📋",
  "index-runbooks": "📖",
  "index-herramientas": "🛠️",
};

const predefinedQuestions = [
  { text: "¿Cuál es el proceso de postmortem blameless?", agent: "Políticas" },
  { text: "¿Cómo resuelvo un CrashLoopBackOff en producción?", agent: "Runbooks" },
  { text: "¿Cómo accedo a Vault para gestionar secretos?", agent: "Herramientas" },
];

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [workflowStep, setWorkflowStep] = useState<WorkflowStep>("idle");
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentInfo | null>(null);
  const [selectedKB, setSelectedKB] = useState<KBInfo | null>(null);
  const [traceLogs, setTraceLogs] = useState<TraceLog[]>([]);

  const addLog = (type: TraceLog["type"], message: string) => {
    // Removed fractionalSecondDigits for broader TS lib compatibility
    const timestamp = new Date().toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    setTraceLogs((prev) => [...prev, { timestamp, type, message }]);
  };

  const handleAgentClick = (agent: AgentInfo) => {
    if (selectedAgent?.id === agent.id) {
      setSelectedAgent(null);
    } else {
      setSelectedAgent(agent);
      setSelectedKB(null);
    }
  };

  const handleKBClick = (kb: KBInfo) => {
    if (selectedKB?.id === kb.id) {
      setSelectedKB(null);
    } else {
      setSelectedKB(kb);
      setSelectedAgent(null);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const text = messageText || input;
    if (!text.trim()) return;

    // Clear previous conversation and logs
    setMessages([]);
    setTraceLogs([]);

    const userMessage: Message = { role: "user", content: text };
    setMessages([userMessage]);
    setInput("");
    setIsLoading(true);
    setWorkflowStep("routing");

    addLog("info", `Consulta recibida: "${text}"`);
    addLog("route", "Orquestador analizando la consulta...");

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await response.json();

      // Set workflow step based on agent
      const agentType = data.agent?.replace("-agent", "") || "politicas";
      setWorkflowStep(agentType as WorkflowStep);
      setActiveAgent(data.agent || null);

      const kbMap: Record<string, string> = {
        politicas: "index-politicas",
        runbooks: "index-runbooks",
        herramientas: "index-herramientas",
      };
      addLog("route", `Derivado a ${data.agent || "especialista"}`);
      addLog(
        "query",
        `${data.agent} consultando ${kbMap[agentType]} via búsqueda semántica...`
      );

      // Log retrieved documents
      const sources = data.sources as SourceInfo[];
      if (sources && sources.length > 0) {
        const docNames = sources
          .map((s: SourceInfo) => s.title || s.filepath || "documento")
          .join(", ");
        addLog("response", `Recuperado de ${kbMap[agentType]}: ${docNames}`);
      } else {
        addLog("response", `Documentos recuperados de ${kbMap[agentType]}`);
      }

      const assistantMessage: Message = {
        role: "assistant",
        content: data.message,
        agent: data.agent,
        sources: data.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      addLog("info", `Respuesta generada (${data.message.length} chars)`);
      setTimeout(() => setWorkflowStep("complete"), 500);
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Ocurrió un error al procesar la consulta. Intentá de nuevo." },
      ]);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        setWorkflowStep("idle");
        setActiveAgent(null);
      }, 2000);
    }
  };

  // Strongly type the node parameter to avoid TS2367 with 'idle'
  const getNodeStatus = (node: NodeId): "idle" | "active" | "complete" => {
    if (workflowStep === "idle") return "idle";
    if (workflowStep === "complete") return "complete";

    // If we're not idle (handled above), the input node is complete
    if (node === "input" ) return "complete";

    // Orchestrator is active only during 'routing'
    if (node === "orchestrator" && workflowStep === "routing") return "active";

    // If we've moved past routing (and not idle/complete), orchestrator is complete
    if (node === "orchestrator" && workflowStep !== "routing") return "complete";
   
    // The agent node matching the current step is active
    if (node === workflowStep) return "active";

    // All other nodes are idle
    return "idle";

  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-text">DevOps Days</span>
          </div>
        </div>
      </header>

      <div className="main-layout">
        {/* Left Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>Agentes</h3>
            <div className="sidebar-items">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className={`sidebar-item ${selectedAgent?.id === agent.id ? "selected" : ""}`}
                  onClick={() => handleAgentClick(agent)}
                >
                  <span>{agent.name}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="sidebar-section">
            <h3>Bases de Conocimiento</h3>
            <div className="sidebar-items">
              {knowledgeBases.map((kb) => (
                <div
                  key={kb.id}
                  className={`sidebar-item ${selectedKB?.id === kb.id ? "selected" : ""}`}
                  onClick={() => handleKBClick(kb)}
                >
                  <span>{kb.id}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Details Panel */}
          {(selectedAgent || selectedKB) && (
            <div className="details-panel">
              <div className="details-header">
                <span className="details-title">{selectedAgent?.name || selectedKB?.name}</span>
                <button
                  className="details-close"
                  onClick={() => {
                    setSelectedAgent(null);
                    setSelectedKB(null);
                  }}
                >
                  ×
                </button>
              </div>
              <div className="details-content">
                <p className="details-description">
                  {selectedAgent?.description || selectedKB?.description}
                </p>

                <div className="details-section">
                  <span className="details-label">Model</span>
                  <span className="details-value">{selectedAgent?.model || selectedKB?.model}</span>
                </div>

                {selectedAgent && selectedAgent.connectedKB && (
                  <div className="details-section">
                    <span className="details-label">Connected KB</span>
                    <span className="details-badge">{selectedAgent.connectedKB}</span>
                  </div>
                )}

                {selectedKB && (
                  <div className="details-section">
                    <span className="details-label">Retrieval Mode</span>
                    <span className="details-value">{selectedKB.retrievalMode}</span>
                  </div>
                )}

                <div className="details-section">
                  <span className="details-label">Knowledge Sources</span>
                  <div className="details-sources">
                    {(selectedAgent?.knowledgeSources || selectedKB?.knowledgeSources || []).map(
                      (ks) => (
                        <span key={ks} className="details-source-tag">
                          {ks}
                        </span>
                      )
                    )}
                    {selectedAgent?.knowledgeSources?.length === 0 && !selectedKB && (
                      <span className="details-value">Ninguna (solo enrutamiento)</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Workflow Canvas */}
        <main className="canvas">
          <div className="workflow-canvas">
            {/* Input Node */}
            <div className={`workflow-node input-node ${getNodeStatus("input")}`}>
              <div className="node-status"></div>
              <div className="node-content">
                <span className="node-title">Entrada</span>
              </div>
              <div className="node-meta">Consulta de texto</div>
            </div>

            <div className="connector vertical"></div>

            {/* Orchestrator Node */}
            <div className={`workflow-node orchestrator-node ${getNodeStatus("orchestrator")}`}>
              <div className="node-status"></div>
              <div className="node-content">
                <span className="node-title">Orquestador</span>
              </div>
              <div className="node-description">Enruta al agente especialista</div>
              <div className="node-badge">gpt-4o</div>
            </div>

            <div className="connector-branch">
              <div className="branch-line left"></div>
              <div className="branch-line center"></div>
              <div className="branch-line right"></div>
            </div>

            {/* Agent Nodes */}
            <div className="agent-row">
              <div className={`workflow-node agent-node politicas ${getNodeStatus("politicas")}`}>
                <div className="node-status"></div>
                <div className="node-content">
                  <span className="node-title">Agente Políticas</span>
                </div>
                <div className="node-kb">
                  <span className="kb-badge">index-politicas</span>
                </div>
              </div>

              <div className={`workflow-node agent-node runbooks ${getNodeStatus("runbooks")}`}>
                <div className="node-status"></div>
                <div className="node-content">
                  <span className="node-title">Agente Runbooks</span>
                </div>
                <div className="node-kb">
                  <span className="kb-badge">index-runbooks</span>
                </div>
              </div>

              <div className={`workflow-node agent-node herramientas ${getNodeStatus("herramientas")}`}>
                <div className="node-status"></div>
                <div className="node-content">
                  <span className="node-title">Agente Herramientas</span>
                </div>
                <div className="node-kb">
                  <span className="kb-badge">index-herramientas</span>
                </div>
              </div>
            </div>

            <div className="connector-merge">
              <div className="merge-line left"></div>
              <div className="merge-line center"></div>
              <div className="merge-line right"></div>
            </div>

            {/* Output Node */}
            <div className={`workflow-node output-node ${workflowStep === "complete" ? "complete" : "idle"}`}>
              <div className="node-status"></div>
              <div className="node-content">
                <span className="node-title">Respuesta</span>
              </div>
              <div className="node-meta">Respuesta fundamentada</div>
            </div>
          </div>

          {/* Trace Logs Panel */}
          <div className="trace-panel">
            <div className="trace-header">
              <span className="trace-title">Traza de ejecución</span>
              {traceLogs.length > 0 && (
                <button className="trace-clear" onClick={() => setTraceLogs([])}>
                  Limpiar
                </button>
              )}
            </div>
            <div className="trace-logs">
              {traceLogs.length === 0 ? (
                <div className="trace-empty">Esperando ejecución de consulta...</div>
              ) : (
                traceLogs.map((log, i) => (
                  <div key={i} className={`trace-log ${log.type}`}>
                    <span className="trace-time">{log.timestamp}</span>
                    <span className={`trace-type ${log.type}`}>
                      {log.type === "info"
                        ? "INFO"
                        : log.type === "route"
                        ? "ROUTE"
                        : log.type === "query"
                        ? "QUERY"
                        : "RESP"}
                    </span>
                    <span className="trace-msg">{log.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </main>

        {/* Chat Panel */}
        <aside className="chat-panel">
          <div className="chat-header">
            <h2>Chat</h2>
            <div className="chat-status">
              {isLoading && <span className="status-dot pulse"></span>}
              <span>{isLoading ? "Procesando..." : "Listo"}</span>
            </div>
          </div>

          <div className="quick-actions">
            {predefinedQuestions.map((q, i) => (
              <button
                key={i}
                className="quick-action-btn"
                onClick={() => sendMessage(q.text)}
                disabled={isLoading}
              >
                {q.text}
              </button>
            ))}
          </div>

          <div className="messages">
            {messages.length === 0 && (
              <div className="empty-state">
                <div className="empty-text">Iniciá una conversación</div>
                <div className="empty-subtext">Hacé una pregunta o usá los accesos rápidos de arriba</div>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.agent && (
                  <div className="message-header">
                    <img src="/assets/capi.png" alt="DevOps Days" className="agent-icon-img" />
                    <span className="agent-name">{msg.agent}</span>
                  </div>
                )}
                <div
                  className="message-content"
                  dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                />
                {msg.agent && (
                  <div className="message-sources">
                    <span className="source-label">Fuentes:</span>
                    <div className="source-list">
                      {msg.sources && msg.sources.length > 0 ? (
                        msg.sources.map((src, idx) => (
                          <span key={idx} className="source-doc">
                            <span className="source-doc-title">{src.title || src.filepath || "Document"}</span>
                            <span className="source-doc-kb">({src.kb})</span>
                          </span>
                        ))
                      ) : (
                        <span className="source-name">
                          {msg.agent.replace("-agent", "") === "politicas"
                            ? "index-politicas"
                            : msg.agent.replace("-agent", "") === "runbooks"
                            ? "index-runbooks"
                            : "index-herramientas"}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="message assistant loading">
                <div className="loading-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="loading-text">
                  {workflowStep === "routing" ? "Enrutando consulta..." : `${activeAgent} procesando...`}
                </span>
              </div>
            )}
          </div>

          <div className="input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Hacé una pregunta..."
              disabled={isLoading}
            />
            <button onClick={() => sendMessage()} disabled={isLoading || !input.trim()}>
              Enviar
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
