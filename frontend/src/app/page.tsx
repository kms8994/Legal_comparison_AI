"use client";

import type { FormEvent } from "react";
import { useState } from "react";

type CaseTone = "green" | "orange";
type InputMode = "natural_language" | "case_number";

type CasePanelData = {
  label: string;
  court: string;
  date: string;
  outcome: string;
  tone: CaseTone;
  issue: string;
  statutes: string;
};

type Candidate = {
  title: string;
  outcome: string;
  summary: string;
  reason: string;
};

type ComparisonData = {
  query: string;
  referenceCase: CasePanelData;
  oppositeCase: CasePanelData;
  keyDifferences: string[];
  commonPoints: string[];
  shortExplanation: string;
  candidates: Candidate[];
  disclaimer: string;
};

type CompareApiResponse = {
  status?: "ready";
  query: string;
  reference_case: {
    case_number: string;
    decision_date: string;
    outcome: string;
    issue_summary: string;
    statutes: string[];
  };
  opposite_case: {
    case_number: string;
    decision_date: string;
    outcome: string;
    issue_summary: string;
    statutes: string[];
  };
  analysis: {
    key_differences: string[];
    common_points: string[];
    short_explanation: string;
  };
  other_candidates: {
    case_number: string;
    outcome: string;
    issue_summary: string;
    reason: string;
  }[];
  disclaimer: string;
};

type ClarificationApiResponse = {
  status: "needs_clarification";
  query: string;
  extracted_facts: Record<string, unknown>;
  questions: {
    slot: string;
    label: string;
    question: string;
    reason: string;
    example: string;
  }[];
  guidance: string;
};

type InsufficientDataApiResponse = {
  status: "insufficient_data";
  query: string;
  reason: string;
  extracted_facts?: Record<string, unknown> | null;
  suggestions: string[];
};

type ApiResponse = CompareApiResponse | ClarificationApiResponse | InsufficientDataApiResponse;

const defaultQuery =
  "신호등 없는 교차로에서 좌회전 차량과 직진 차량이 충돌한 교통사고";
const defaultCaseNumber = "대법원 2019다2345";

const defaultComparison: ComparisonData = {
  query: defaultQuery,
  referenceCase: {
    label: "기준 판례",
    court: "대법원 2019다2345 판결",
    date: "2019.06.27",
    outcome: "인용",
    tone: "green",
    issue:
      "신호등 없는 교차로에서 직진 차량과 좌회전 차량이 충돌한 사고에서 직진 차량의 과실 범위가 문제된 사건",
    statutes: "도로교통법 제5조, 제7조, 민법 제750조"
  },
  oppositeCase: {
    label: "다른 결론 판례",
    court: "대법원 2018다3456 판결",
    date: "2018.08.13",
    outcome: "기각",
    tone: "orange",
    issue:
      "교차로에서 좌회전 차량과 직진 차량이 충돌했지만 좌회전 차량의 진입 방식과 확인 의무가 더 크게 문제된 사건",
    statutes: "도로교통법 제5조, 제7조, 민법 제750조"
  },
  keyDifferences: [
    "기준 판례는 직진 차량의 과속과 전방주시의무 위반을 더 크게 보았습니다.",
    "다른 결론 판례는 좌회전 차량의 진입 방식과 안전 확인 의무 위반을 더 중요하게 판단했습니다."
  ],
  commonPoints: [
    "두 판례 모두 신호등 없는 교차로에서 발생한 충돌 사고입니다.",
    "두 판례 모두 교차로 통행 방법과 운전자의 주의의무가 쟁점이었습니다.",
    "도로교통법과 민법상 손해배상 책임이 함께 검토되었습니다."
  ],
  shortExplanation:
    "두 판례는 사고 유형과 적용 조문은 비슷하지만, 법원이 중요하게 본 주의의무 위반 주체가 달라 최종 결론이 달라졌습니다.",
  candidates: [
    {
      title: "대법원 2021다6789 판결",
      outcome: "인용",
      summary: "교차로 충돌 사고에서 직진 차량의 과속 여부가 문제된 사건",
      reason: "같은 조문과 유사한 쟁점"
    },
    {
      title: "서울고등법원 2020나4567 판결",
      outcome: "인용",
      summary: "좌회전 차량과 직진 차량의 통행 우선순위가 문제된 사건",
      reason: "같은 사고 유형"
    }
  ],
  disclaimer:
    "이 비교 설명은 학습과 검토를 돕기 위한 보조 정보입니다. 실제 판단 전에는 반드시 원문을 확인하세요."
};

function Badge({ children, tone }: { children: string; tone: CaseTone }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function CasePanel({ data }: { data: CasePanelData }) {
  return (
    <article className={`case-panel ${data.tone}`}>
      <div className="panel-kicker">{data.label}</div>
      <div className="case-heading">
        <h3>{data.court}</h3>
        <Badge tone={data.tone}>{data.outcome}</Badge>
      </div>
      <p className="case-meta">{data.date}</p>
      <p className="case-issue">{data.issue}</p>
      <div className="statutes">
        <span>참조조문</span>
        <strong>{data.statutes}</strong>
      </div>
      <a className="text-link" href="#">
        원문 보기
      </a>
    </article>
  );
}

function toComparisonData(response: CompareApiResponse): ComparisonData {
  return {
    query: response.query,
    referenceCase: {
      label: "기준 판례",
      court: `${response.reference_case.case_number} 판결`,
      date: response.reference_case.decision_date,
      outcome: response.reference_case.outcome,
      tone: "green",
      issue: response.reference_case.issue_summary,
      statutes: response.reference_case.statutes.join(", ")
    },
    oppositeCase: {
      label: "다른 결론 판례",
      court: `${response.opposite_case.case_number} 판결`,
      date: response.opposite_case.decision_date,
      outcome: response.opposite_case.outcome,
      tone: "orange",
      issue: response.opposite_case.issue_summary,
      statutes: response.opposite_case.statutes.join(", ")
    },
    keyDifferences: response.analysis.key_differences,
    commonPoints: response.analysis.common_points,
    shortExplanation: response.analysis.short_explanation,
    candidates: response.other_candidates.map((candidate) => ({
      title: `${candidate.case_number} 판결`,
      outcome: candidate.outcome,
      summary: candidate.issue_summary,
      reason: candidate.reason
    })),
    disclaimer: response.disclaimer
  };
}

export default function Home() {
  const [inputMode, setInputMode] = useState<InputMode>("natural_language");
  const [description, setDescription] = useState("");
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [clarification, setClarification] = useState<ClarificationApiResponse | null>(null);
  const [insufficientData, setInsufficientData] = useState<InsufficientDataApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function runCompare() {
    const query =
      description.trim() || (inputMode === "case_number" ? defaultCaseNumber : defaultQuery);

    if (inputMode === "natural_language" && query.length < 5) {
      setNotice("사건 설명을 조금 더 구체적으로 입력해 주세요.");
      return;
    }

    if (inputMode === "case_number" && query.length < 2) {
      setNotice("사건번호를 입력해 주세요.");
      return;
    }

    setIsLoading(true);
    setNotice(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
      const response = await fetch(`${baseUrl}/api/compare`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          description: query,
          query_type: inputMode
        })
      });

      if (!response.ok) {
        throw new Error("compare request failed");
      }

      const data = (await response.json()) as ApiResponse;
      if (data.status === "needs_clarification") {
        setClarification(data);
        setInsufficientData(null);
        setComparison(null);
        return;
      }
      if (data.status === "insufficient_data") {
        setInsufficientData(data);
        setClarification(null);
        setComparison(null);
        return;
      }
      setClarification(null);
      setInsufficientData(null);
      setComparison(toComparisonData(data));
    } catch {
      setComparison({ ...defaultComparison, query });
      setNotice("백엔드 연결 전이라 예시 판례 비교를 표시합니다.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleCompare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runCompare();
  }

  function handleModeChange(mode: InputMode) {
    setInputMode(mode);
    setDescription("");
    setNotice(null);
  }

  function resetSearch() {
    setComparison(null);
    setClarification(null);
    setInsufficientData(null);
    setNotice(null);
    setDescription("");
    setInputMode("natural_language");
  }

  return (
    <main className={comparison ? "app-shell result-mode" : "app-shell start-mode"}>
      <nav className="topbar">
        <a className="brand" href="#" onClick={resetSearch}>
          <span className="brand-mark">§</span>
          <span>판례비교</span>
        </a>
        <a className="guide-link" href="#">
          이용 가이드
        </a>
      </nav>

      {!comparison ? (
        <section className="start-page">
          <div className="start-copy">
            <p className="eyebrow">자연어 기반 판례 비교</p>
            <h1>사건을 설명하면, 비교할 판례를 찾아드립니다.</h1>
            <p>
              사건번호를 몰라도 괜찮습니다. 사실관계와 쟁점을 자연어로 적으면 기준 판례와
              결론이 다른 판례를 함께 비교합니다.
            </p>
          </div>

          <form className="start-search" onSubmit={handleCompare}>
            <div className="input-mode-field">
              <label htmlFor="input-mode">입력 방식</label>
              <select
                id="input-mode"
                value={inputMode}
                onChange={(event) => handleModeChange(event.target.value as InputMode)}
              >
                <option value="natural_language">자연어 설명</option>
                <option value="case_number">사건번호</option>
              </select>
            </div>

            <label htmlFor="case-description">
              {inputMode === "case_number" ? "사건번호" : "사건 설명"}
            </label>
            {inputMode === "case_number" ? (
              <input
                id="case-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder={defaultCaseNumber}
                aria-label="사건번호"
              />
            ) : (
              <textarea
                id="case-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder={defaultQuery}
                aria-label="사건 자연어 설명"
                rows={4}
              />
            )}
            {notice ? <p className="notice">{notice}</p> : null}
            {clarification ? (
              <section className="clarification-box" aria-label="추가 입력 요청">
                <p>{clarification.guidance}</p>
                <div className="clarification-list">
                  {clarification.questions.map((item) => (
                    <article key={item.slot}>
                      <strong>{item.label}</strong>
                      <p>{item.question}</p>
                      <span>{item.example}</span>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}
            {insufficientData ? (
              <section className="data-empty-box" aria-label="데이터 부족 안내">
                <strong>관련 판례 데이터가 아직 부족합니다.</strong>
                <p>{insufficientData.reason}</p>
                <ul>
                  {insufficientData.suggestions.map((suggestion) => (
                    <li key={suggestion}>{suggestion}</li>
                  ))}
                </ul>
              </section>
            ) : null}
            <div className="start-actions">
              <button type="button" onClick={() => void runCompare()} disabled={isLoading}>
                {isLoading ? "판례 찾는 중" : "판례 비교하기"}
              </button>
            </div>
            <p className="start-example">
              예시: {inputMode === "case_number" ? defaultCaseNumber : defaultQuery}
            </p>
          </form>

          <p className="start-disclaimer">
            이 서비스는 판례 검색과 비교를 보조하는 학습 도구입니다.
          </p>
        </section>
      ) : (
        <>
          <section className="result-header">
            <button className="back-button" onClick={resetSearch}>
              다시 입력하기
            </button>
            <div>
              <p className="eyebrow">판례 비교 워크스페이스</p>
              <h1>{comparison.query}</h1>
            </div>
          </section>

          <section className="workspace" aria-label="판례 비교 결과">
            <div className="comparison-grid">
              <CasePanel data={comparison.referenceCase} />
              <div className="vs" aria-hidden="true">
                vs
              </div>
              <CasePanel data={comparison.oppositeCase} />
            </div>

            <section className="analysis-card">
              <div className="analysis-section highlight">
                <div>
                  <span className="section-icon orange-dot" />
                  <h2>핵심 차이</h2>
                </div>
                <ul>
                  {comparison.keyDifferences.map((difference) => (
                    <li key={difference}>{difference}</li>
                  ))}
                </ul>
              </div>
              <div className="analysis-section">
                <div>
                  <span className="section-icon green-dot" />
                  <h2>공통점</h2>
                </div>
                <ul>
                  {comparison.commonPoints.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
              </div>
              <div className="analysis-note">
                <h2>직관적 비교 설명</h2>
                <p>{comparison.shortExplanation}</p>
              </div>
            </section>

            <aside className="candidate-strip">
              <div>
                <p className="candidate-title">추가 확인 후보</p>
                <p className="candidate-copy">
                  같은 법영역, 사건유형, 참조조문을 가진 판례를 함께 확인할 수 있습니다.
                </p>
              </div>
              <div className="candidate-list">
                {comparison.candidates.map((candidate) => (
                  <article key={candidate.title}>
                    <div>
                      <strong>{candidate.title}</strong>
                      <Badge tone="green">{candidate.outcome}</Badge>
                    </div>
                    <p>{candidate.summary}</p>
                    <span>{candidate.reason}</span>
                  </article>
                ))}
              </div>
            </aside>
          </section>

          <footer className="disclaimer">{comparison.disclaimer}</footer>
        </>
      )}
    </main>
  );
}
