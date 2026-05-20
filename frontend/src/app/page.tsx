"use client";

import { useState } from "react";

type CaseTone = "green" | "orange";

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

const defaultQuery = "신호 없는 교차로에서 좌회전 차량과 직진 차량이 충돌한 사건";

const defaultComparison: ComparisonData = {
  query: defaultQuery,
  referenceCase: {
    label: "기준 판례",
    court: "대법원 2019다12345 판결",
    date: "2019.06.27",
    outcome: "인용",
    tone: "green",
    issue:
      "신호 없는 교차로에서 직진 차량과 좌회전 차량이 충돌한 사고에서 직진 차량의 과실 범위가 문제된 사건",
    statutes: "도로교통법 제25조, 제27조, 민법 제750조"
  },
  oppositeCase: {
    label: "반대 결론 판례",
    court: "대법원 2018다23456 판결",
    date: "2018.08.13",
    outcome: "기각",
    tone: "orange",
    issue:
      "교차로에서 좌회전 차량과 직진 차량이 충돌한 사고에서 좌회전 차량의 과실이 더 크다고 본 사건",
    statutes: "도로교통법 제25조, 제27조, 민법 제750조"
  },
  keyDifferences: [
    "기준 판례는 직진 차량의 과속과 주의의무 위반을 더 크게 보았습니다.",
    "반대 결론 판례는 좌회전 차량의 진입 방식과 확인 의무 위반을 더 크게 보았습니다."
  ],
  commonPoints: [
    "두 판례 모두 신호 없는 교차로에서 발생한 충돌 사고입니다.",
    "두 판례 모두 교차로 통행 방법과 운전자의 주의의무가 문제되었습니다.",
    "도로교통법과 민법상 손해배상 책임이 함께 검토되었습니다."
  ],
  shortExplanation:
    "두 판례는 사고 유형과 적용 조문이 유사하지만, 법원이 더 중요하게 본 주의의무 위반 주체가 달라 최종 결론이 달라졌습니다.",
  candidates: [
    {
      title: "대법원 2021다56789 판결",
      outcome: "인용",
      summary: "교차로 충돌 사고에서 직진 차량의 과속 여부가 문제된 사건",
      reason: "같은 조문 · 유사한 쟁점"
    },
    {
      title: "서울고등법원 2020나34567 판결",
      outcome: "인용",
      summary: "좌회전 차량과 직진 차량의 통행 우선순위가 문제된 사건",
      reason: "같은 조문 · 사고 유형 유사"
    }
  ],
  disclaimer:
    "본 비교 설명은 AI가 생성한 학습 보조 정보입니다. 실제 판단 전 원문을 반드시 확인해 주세요."
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

function toComparisonData(response: any): ComparisonData {
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
      label: "반대 결론 판례",
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
    candidates: response.other_candidates.map((candidate: any) => ({
      title: `${candidate.case_number} 판결`,
      outcome: candidate.outcome,
      summary: candidate.issue_summary,
      reason: candidate.reason
    })),
    disclaimer: response.disclaimer
  };
}

export default function Home() {
  const [description, setDescription] = useState("");
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function handleCompare() {
    const query = description.trim();

    if (query.length < 5) {
      setNotice("사건 설명을 조금 더 구체적으로 입력해 주세요.");
      return;
    }

    setIsLoading(true);
    setNotice(null);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
      const response = await fetch(`${baseUrl}/api/compare`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ description: query })
      });

      if (!response.ok) {
        throw new Error("compare request failed");
      }

      const data = await response.json();
      setComparison(toComparisonData(data));
    } catch {
      setComparison({ ...defaultComparison, query });
      setNotice("백엔드 연결 전까지는 예시 판례 비교를 표시합니다.");
    } finally {
      setIsLoading(false);
    }
  }

  function resetSearch() {
    setComparison(null);
    setNotice(null);
  }

  return (
    <main className={comparison ? "app-shell result-mode" : "app-shell start-mode"}>
      <nav className="topbar">
        <a className="brand" href="#" onClick={resetSearch}>
          <span className="brand-mark">⚖</span>
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
              사건번호를 몰라도 괜찮습니다. 사실관계와 쟁점을 자연어로 적으면
              기준 판례와 결론이 다른 판례를 함께 비교합니다.
            </p>
          </div>

          <div className="start-search">
            <label htmlFor="case-description">사건 설명</label>
            <textarea
              id="case-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder={defaultQuery}
              aria-label="사건 자연어 설명"
              rows={4}
            />
            {notice ? <p className="notice">{notice}</p> : null}
            <div className="start-actions">
              <button onClick={handleCompare} disabled={isLoading}>
                {isLoading ? "판례 찾는 중" : "판례 비교하기"}
              </button>
            </div>
            <p className="start-example">예시: {defaultQuery}</p>
          </div>

          <p className="start-disclaimer">
            본 서비스는 판례 검색 및 비교를 보조하는 학습 도구입니다.
          </p>
        </section>
      ) : (
        <>
          <section className="result-header">
            <button className="back-button" onClick={resetSearch}>
              ← 다시 입력하기
            </button>
            <div>
              <p className="eyebrow">입력한 사건</p>
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
                <h2>짧은 비교 설명</h2>
                <p>{comparison.shortExplanation}</p>
              </div>
            </section>

            <aside className="candidate-strip">
              <div>
                <p className="candidate-title">다른 비교 후보</p>
                <p className="candidate-copy">
                  같은 조문이나 유사한 쟁점을 가진 판례를 추가로 확인할 수 있습니다.
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
