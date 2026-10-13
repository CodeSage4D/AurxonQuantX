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
  fair_value_dcf?: number | null;
  dcf_upside_percent?: number | null;
  graham_number: number;
  graham_upside_percent: number;
  pe_ratio: number;
  pb_ratio: number;
  piotroski_f_score: number;
  altman_z_score?: number | null;
  dividend_yield_percent: number;
  is_undervalued: boolean;
  is_financial_institution?: boolean;
  sector_exclusion_notes?: string | null;
  dcf_sensitivity_matrix?: Record<string, Record<string, number>> | null;
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
  sequence_id?: number;
  audit_id: string;
  ticker: string;
  query: string;
  recommendation: string;
  current_price: number;
  fair_value_dcf?: number | null;
  graham_number: number;
  evidence_score: number;
  uncertainty_level: string;
  content_sha256: string;
  chained_hash?: string;
  created_at: string;
}

// ============================================================================
// PHASE 2 TYPES: IPO INTELLIGENCE & MUTUAL FUNDS
// ============================================================================

export interface IssueStructure {
  issuer_name: string;
  symbol?: string;
  price_band_floor: number;
  price_band_cap: number;
  face_value: number;
  lot_size: number;
  fresh_issue_crores: number;
  offer_for_sale_crores: number;
  total_issue_crores: number;
  pre_issue_shares_cr: number;
  post_issue_shares_cr: number;
  dilution_percent: number;
  promoter_holding_pre_percent: number;
  promoter_holding_post_percent: number;
  use_of_proceeds: Record<string, number>;
  reservation_qib_pct: number;
  reservation_nii_pct: number;
  reservation_retail_pct: number;
}

export interface DisclosedRiskFactor {
  risk_id: string;
  category: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  page_reference?: number;
  financial_impact_note: string;
  is_corroborated_independently: boolean;
}

export interface PeerComparison {
  peer_name: string;
  pe_ratio: number;
  pb_ratio: number;
  roe_pct: number;
  revenue_crores: number;
  pat_margin_pct: number;
}

export interface IPOFinancials {
  periods: string[];
  revenue_crores: number[];
  ebitda_crores: number[];
  pat_crores: number[];
  operating_cash_flow_crores: number[];
  revenue_cagr_3y_pct: number;
  ebitda_margin_latest_pct: number;
  pat_margin_latest_pct: number;
  roe_latest_pct: number;
  roce_latest_pct: number;
  debt_to_equity: number;
  customer_concentration_top5_pct: number;
}

export interface IPOValuationAnalysis {
  market_cap_at_cap_crores: number;
  pe_at_floor: number;
  pe_at_cap: number;
  industry_average_pe: number;
  valuation_premium_discount_pct: number;
  peers: PeerComparison[];
  scenarios: Record<string, number>;
}

export interface IPODossier {
  audit_id: string;
  issuer_name: string;
  filing_type: string;
  structure: IssueStructure;
  financials: IPOFinancials;
  risks: DisclosedRiskFactor[];
  valuation: IPOValuationAnalysis;
  business_quality_verdict: string;
  financial_quality_verdict: string;
  governance_risk_verdict: string;
  valuation_verdict: string;
  proceeds_utility_verdict: string;
  listing_speculation_vs_long_term: string;
  key_unresolved_facts: string[];
  overall_recommendation: string;
  evidence_score: number;
  created_at: string;
}

export interface HoldingItem {
  company_name: string;
  symbol: string;
  weight_pct: number;
  sector: string;
}

export interface FundIdentity {
  scheme_code: string;
  scheme_name: string;
  amc_name: string;
  category: string;
  benchmark_index: string;
  plan: string;
  option: string;
  expense_ratio_pct: number;
  regular_expense_ratio_pct?: number | null;
  aum_crores: number;
  exit_load: string;
  inception_date: string;
  is_passive: boolean;
  tracking_index?: string | null;
}

export interface FundRiskReturnMetrics {
  cagr_1y_pct: number;
  cagr_3y_pct: number;
  cagr_5y_pct: number;
  cagr_since_inception_pct: number;
  rolling_return_3y_min_pct: number;
  rolling_return_3y_median_pct: number;
  rolling_return_3y_max_pct: number;
  annualized_volatility_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  alpha_vs_benchmark_pct: number;
  beta_vs_benchmark: number;
  tracking_error_pct?: number | null;
  tracking_difference_pct?: number | null;
  top_10_holdings_pct: number;
  top_3_sectors_pct: number;
  holdings: HoldingItem[];
}

export interface FundComparisonResult {
  schemes: FundIdentity[];
  metrics: Record<string, FundRiskReturnMetrics>;
  pairwise_overlap_pct: Record<string, number>;
  direct_vs_regular_savings_10y_lakhs: number;
  comparison_notes: string[];
}

export interface PortfolioAllocationPlan {
  audit_id: string;
  goal_name: string;
  horizon_years: number;
  risk_profile: string;
  recommended_equity_pct: number;
  recommended_debt_pct: number;
  recommended_gold_pct: number;
  allocated_schemes: Array<Record<string, any>>;
  downside_stress_scenario_drawdown_pct: number;
  key_risks_and_caveats: string[];
  created_at: string;
}

export interface SourceRegistration {
  source_id: string;
  name: string;
  category: string;
  access_method: string;
  base_url_or_pattern: string;
  reliability_weight: number;
  update_frequency: string;
  attribution_notice: string;
  fallback_behavior: string;
}
