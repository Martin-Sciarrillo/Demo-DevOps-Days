import { useState } from "react";

const VENDORS: { match: (url: string) => boolean; name: string; color: string; bg: string }[] = [
  { match: (u) => u.includes("aws.amazon.com") || u.includes("amazon.com"), name: "AWS", color: "#FF9900", bg: "#FFF3E0" },
  { match: (u) => u.includes("hashicorp.com/terraform") || u.includes("registry.terraform.io"), name: "Terraform", color: "#7B42BC", bg: "#F3E8FF" },
  { match: (u) => u.includes("hashicorp.com/vault") || u.includes("hashicorp.com/consul"), name: "HashiCorp", color: "#1B1B1B", bg: "#F0F0F0" },
  { match: (u) => u.includes("pagerduty.com"), name: "PagerDuty", color: "#06AC38", bg: "#E8F8ED" },
  { match: (u) => u.includes("ansible.com") || u.includes("galaxy.ansible.com"), name: "Ansible", color: "#EE0000", bg: "#FEE8E8" },
];

const INTERNAL_KS: Record<string, { name: string; color: string; bg: string }> = {
  "ks-politicas":    { name: "Wiki Políticas",   color: "#6366F1", bg: "#EEF2FF" },
  "ks-runbooks":     { name: "Wiki Runbooks",     color: "#0EA5E9", bg: "#E0F2FE" },
  "ks-herramientas": { name: "Wiki Herramientas", color: "#059669", bg: "#D1FAE5" },
  "index-politicas":    { name: "Wiki Políticas",   color: "#6366F1", bg: "#EEF2FF" },
  "index-runbooks":     { name: "Wiki Runbooks",     color: "#0EA5E9", bg: "#E0F2FE" },
  "index-herramientas": { name: "Wiki Herramientas", color: "#059669", bg: "#D1FAE5" },
};

function detectVendor(url: string, activitySource?: string | number): { name: string; color: string; bg: string } {
  // 1. activity_source identifica el KS interno exacto — normalizar a string
  const actStr = activitySource != null ? String(activitySource) : "";
  if (actStr) {
    for (const [key, val] of Object.entries(INTERNAL_KS)) {
      if (actStr.includes(key)) return val;
    }
  }
  // 2. URL de dominio externo
  for (const v of VENDORS) {
    if (v.match(url)) return { name: v.name, color: v.color, bg: v.bg };
  }
  // 3. URL path interno (wiki-interno/politicas/...)
  if (url.includes("politicas")) return INTERNAL_KS["ks-politicas"];
  if (url.includes("runbooks"))  return INTERNAL_KS["ks-runbooks"];
  if (url.includes("herramientas")) return INTERNAL_KS["ks-herramientas"];
  // 4. fallback
  return { name: "Interno", color: "#6366F1", bg: "#EEF2FF" };
}

const formatMarkdown = (text: string): string => {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br />");
};

interface SourceInfo {
  kb?: string;
  title?: string;
  filepath?: string;
  url?: string;
  score?: number;
  activity_source?: string | number;
  reference_type?: string;
  doc_key?: string;
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

interface KnowledgeSource {
  name: string;
  type: "internal" | "web";
  url?: string;
  vendor?: string;
}

interface KBInfo {
  id: string;
  name: string;
  icon: string;
  description: string;
  retrievalMode: string;
  model: string;
  knowledgeSources: KnowledgeSource[];
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
    id: "kb-politicas",
    name: "KB Políticas",
    icon: "",
    description: "Políticas de on-call, guardia, escalado, SLA/SLO, postmortem, cultura blameless y certificaciones.",
    retrievalMode: "Agentic Retrieval",
    model: "gpt-4o",
    knowledgeSources: [
      { name: "Wiki Políticas (interno)", type: "internal" },
      { name: "AWS Well-Architected", type: "web", url: "https://docs.aws.amazon.com/wellarchitected", vendor: "AWS" },
      { name: "PagerDuty Support Docs", type: "web", url: "https://support.pagerduty.com", vendor: "PagerDuty" },
    ],
  },
  {
    id: "kb-runbooks",
    name: "KB Runbooks",
    icon: "",
    description: "Runbooks operacionales, playbooks de incidentes, procedimientos de respuesta a alertas y troubleshooting.",
    retrievalMode: "Agentic Retrieval",
    model: "gpt-4o",
    knowledgeSources: [
      { name: "Wiki Runbooks (interno)", type: "internal" },
      { name: "Terraform Docs", type: "web", url: "https://developer.hashicorp.com/terraform", vendor: "Terraform" },
      { name: "AWS EKS & Systems Manager", type: "web", url: "https://docs.aws.amazon.com/eks", vendor: "AWS" },
    ],
  },
  {
    id: "kb-herramientas",
    name: "KB Herramientas",
    icon: "",
    description: "Catálogo de herramientas de infraestructura, CI/CD, monitoring, observabilidad y gestión de secretos.",
    retrievalMode: "Agentic Retrieval",
    model: "gpt-4o",
    knowledgeSources: [
      { name: "Wiki Herramientas (interno)", type: "internal" },
      { name: "Ansible Docs", type: "web", url: "https://docs.ansible.com", vendor: "Ansible" },
      { name: "HashiCorp Vault & Consul", type: "web", url: "https://developer.hashicorp.com/vault", vendor: "HashiCorp" },
    ],
  },
];


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

      const kbName = kbMap[agentType] || agentType;
      addLog("query", `Foundry IQ: analizando intent sobre ${kbName}...`);
      addLog("query", `Consultando knowledge sources (interno + multi-vendor)...`);

      const sources = data.sources as SourceInfo[];
      if (sources && sources.length > 0) {
        const vendorSet = new Set(sources.map((s) => detectVendor(s.url || "", s.activity_source).name));
        const vendorList = Array.from(vendorSet).join(", ");
        addLog("response", `Foundry IQ recuperó ${sources.length} fuentes: ${vendorList}`);
        addLog("response", `Re-ranking y síntesis completados → respuesta generada`);
      } else {
        addLog("response", `Foundry IQ consultó ${kbName} → respuesta sintetizada`);
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
                    {selectedAgent && selectedAgent.knowledgeSources.length === 0 && (
                      <span className="details-value">Ninguna (solo enrutamiento)</span>
                    )}
                    {selectedAgent && selectedAgent.knowledgeSources.length > 0 && (
                      selectedAgent.knowledgeSources.map((ks) => (
                        <span key={ks} className="details-source-tag">{ks}</span>
                      ))
                    )}
                    {selectedKB && selectedKB.knowledgeSources.map((ks) => {
                      const vendor = ks.vendor ? detectVendor(ks.url || "", ks.vendor) : detectVendor("", "ks-" + selectedKB.id.replace("kb-",""));
                      return (
                        <div key={ks.name} className="details-ks-row">
                          <span
                            className="details-ks-badge"
                            style={{ background: vendor.bg, color: vendor.color, borderColor: vendor.color + "44" }}
                          >
                            {ks.type === "internal" ? "Interno" : ks.vendor}
                          </span>
                          {ks.url ? (
                            <a href={ks.url} target="_blank" rel="noreferrer" className="details-ks-name">
                              {ks.name}
                            </a>
                          ) : (
                            <span className="details-ks-name">{ks.name}</span>
                          )}
                        </div>
                      );
                    })}
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
                  <span className="kb-badge">kb-politicas</span>
                </div>
                <div className="node-sources">
                  <span className="node-source-tag internal">Wiki</span>
                  <span className="node-source-tag aws">AWS</span>
                  <span className="node-source-tag pagerduty">PagerDuty</span>
                </div>
              </div>

              <div className={`workflow-node agent-node runbooks ${getNodeStatus("runbooks")}`}>
                <div className="node-status"></div>
                <div className="node-content">
                  <span className="node-title">Agente Runbooks</span>
                </div>
                <div className="node-kb">
                  <span className="kb-badge">kb-runbooks</span>
                </div>
                <div className="node-sources">
                  <span className="node-source-tag internal">Wiki</span>
                  <span className="node-source-tag terraform">Terraform</span>
                  <span className="node-source-tag aws">AWS</span>
                </div>
              </div>

              <div className={`workflow-node agent-node herramientas ${getNodeStatus("herramientas")}`}>
                <div className="node-status"></div>
                <div className="node-content">
                  <span className="node-title">Agente Herramientas</span>
                </div>
                <div className="node-kb">
                  <span className="kb-badge">kb-herramientas</span>
                </div>
                <div className="node-sources">
                  <span className="node-source-tag internal">Wiki</span>
                  <span className="node-source-tag ansible">Ansible</span>
                  <span className="node-source-tag hashicorp">HashiCorp</span>
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
                    <img src="/assets/capi.png" alt="Capi" className="agent-icon-img" />
                    <span className="agent-name">{msg.agent}</span>
                  </div>
                )}
                <div
                  className="message-content"
                  dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                />
                {msg.agent && msg.sources && msg.sources.length > 0 && (() => {
                  // Deduplicate by title+url, then sort: Interno first, then by vendor name
                  const seen = new Set<string>();
                  const unique = msg.sources.filter((s) => {
                    const key = (s.title || "") + (s.url || "");
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                  });
                  const sorted = [...unique].sort((a, b) => {
                    const va = detectVendor(a.url || "", a.activity_source).name;
                    const vb = detectVendor(b.url || "", b.activity_source).name;
                    if (va === "Interno" && vb !== "Interno") return -1;
                    if (vb === "Interno" && va !== "Interno") return 1;
                    return va.localeCompare(vb);
                  });
                  // Group by vendor
                  const groups: Record<string, typeof sorted> = {};
                  for (const src of sorted) {
                    const v = detectVendor(src.url || "", src.activity_source).name;
                    if (!groups[v]) groups[v] = [];
                    groups[v].push(src);
                  }
                  return (
                    <div className="message-sources">
                      <span className="source-label">Fuentes Foundry IQ ({unique.length})</span>
                      <div className="source-cards">
                        {Object.entries(groups).map(([vendorName, srcs]) => {
                          const vendor = detectVendor(srcs[0].url || "", srcs[0].activity_source);
                          return (
                            <div key={vendorName} className="source-group">
                              <span
                                className="source-group-header"
                                style={{ color: vendor.color, borderColor: vendor.color + "55" }}
                              >
                                {vendorName} ({srcs.length})
                              </span>
                              {srcs.map((src, idx) => {
                                const title = src.title || "Documento";
                                const score = src.score != null ? Math.round(src.score * 100) / 100 : null;
                                const isExternalUrl = src.url && src.url.startsWith("http");
                                return (
                                  <div key={idx} className="source-card">
                                    {isExternalUrl ? (
                                      <a href={src.url} target="_blank" rel="noreferrer" className="source-card-title">
                                        {title}
                                      </a>
                                    ) : (
                                      <span className="source-card-title" title={src.url || src.doc_key || ""}>
                                        {title}
                                      </span>
                                    )}
                                    {score != null && (
                                      <span className="source-card-score">↑{score}</span>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })()}
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
