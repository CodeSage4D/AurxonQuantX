export type EvidenceStatus = 'VERIFIED' | 'UNCERTAIN' | 'CONTRADICTED' | 'UNVERIFIED';

export type RecommendationType = 'ACCUMULATE' | 'HOLD' | 'AVOID' | 'ABSTAIN_DATA_DEFICIENT';

export interface EvidenceClaim {
  claim_id: string;
  claim_text: string;
  source_name: string;
  source_url: string;
  publication_date?: string;
  retrieval_timestamp: string;
  confidence_score: number;
  verification_status: EvidenceStatus;
  supporting_metrics: Record<string, any>;
  contradiction_notes?: string;
}

export interface DeterministicValuation {
  ticker: string;
  currency: string;
  current_price: number;
  fair_value_dcf: number;
  dcf_upside_percent: number;
  graham_number: number;
  graham_upside_percent: number;
  pe_ratio: number;
  pb_ratio: number;
  piotroski_f_score: number;
  altman_z_score: number;
  dividend_yield_percent: number;
  is_undervalued: boolean;
  calculation_timestamp: string;
  formula_signatures: Record<string, string>;
}

export interface AdversarialCounterThesis {
  bear_case_summary: string;
  key_vulnerabilities: string[];
  downside_risk_factors: string[];
  margin_of_safety_adequate: boolean;
}

export interface ResearchObjective {
  ticker: string;
  query: string;
  asset_class: string;
  horizon: string;
  risk_tolerance: string;
}

export interface ResearchFinding {
  audit_id: string;
  objective: ResearchObjective;
  valuation: DeterministicValuation;
  claims: EvidenceClaim[];
  counter_thesis: AdversarialCounterThesis;
  synthesis_summary: string;
  recommendation: RecommendationType;
  uncertainty_level: string;
  overall_evidence_score: number;
  created_at: string;
}

export interface StreamEvent {
  step: string;
  status: string;
  progress_pct: number;
  data: Record<string, any>;
  timestamp: string;
}

export interface AuditRecordSummary {
  audit_id: string;
  ticker: string;
  query: string;
  recommendation: string;
  current_price: number;
  fair_value_dcf: number;
  graham_number: number;
  evidence_score: number;
  uncertainty_level: string;
  content_sha256: string;
  created_at: string;
}
