# The FedACT Authoritative Research Roadmap

> **Document status:** The authoritative executable research roadmap for FedACT. This document is self-contained and defines the scientific study and implementation contract.
> **Method name:** **FedACT — Federated Action-Certified Threat Dynamics**.
> **Protocol state:** Scientifically defined and fully specified for execution. The Configuration YAML contains configuration data only; fixed scientific, algorithmic, validation, execution, provenance, and reporting semantics are defined in their authoritative roadmap sections.
> **Governing principle:** Preserve scientific completeness, chronological validity, reproducibility, and implementation clarity without introducing post hoc scientific decisions.

---

# PART I — SCIENTIFIC SPECIFICATION

# 1. Roadmap Authority, Contribution Identity, and Status

## 1.1 Authority

This roadmap is the complete operational specification of the FedACT contribution: the federated, chronologically valid identification of a **control-compatible shared threat-transition set** and the certification of **domain-valid defensive actions** whose support interval is decision-identifiable relative to that set, without requiring point-identification of the full latent transition. The exact estimand, algorithm, theory, assumptions, and evidence requirements that ground this roadmap are reproduced directly in Parts I and III rather than left to an external document.

The roadmap defines:

* mathematical verification;
* implementation order;
* scientific dependencies;
* chronology;
* calibration;
* experimental roles;
* baseline roles;
* ablations;
* metrics;
* statistical synthesis;
* failure semantics;
* reproducibility and provenance;
* manuscript evidence generation.

Implementation may operationalize the specified research but may not redesign it.

## 1.2 Contribution identity

The proposed method is exclusively:

# **FedACT**

FedACT terminology:

* FedACT algorithm;
* FedACT feasible transition set;
* FedACT action interval;
* FedACT action certificate;
* FedACT certified action;
* FedACT prospective set;
* FedACT hardening;
* FedACT abstention.

## 1.3 Scientific contract

The following are scientifically fixed:

1. The primary object is a **set-valued shared threat transition**, not a point forecast.
2. The primary decision object is the support interval of a domain-valid action functional.
3. Certification requires worst-case alignment over the complete compatible set.
4. Full transition identification is not required.
5. Decision ambiguity must remain explicit.
6. Abstention is a valid scientific outcome.
7. Federation is scientifically meaningful through complementary control constraints, not generic averaging.
8. All prospective evaluation is strictly chronological.
9. Domain validity and statistical certification are separate requirements.
10. Point estimates may be diagnostic or comparator quantities only.
11. Later-real outcomes may not influence pre-cutoff decisions.
12. Synchronized nuisance outside all controls remains a fundamental non-identification boundary.

# 2. Scientific Scope, Contribution Boundary, and Non-Goals

## 2.1 Scientific problem

For a historical malicious transition observed through organization-specific nuisance, FedACT asks:

> Which domain-valid prospective defensive actions are scientifically supported by the part of threat evolution compatible with all usable distributed control evidence?

It does **not** ask for unrestricted recovery of a complete future malware representation vector.

## 2.2 Primary scientific capability

FedACT must demonstrate that:

> A concrete defensive action can be identified even when the latent transition remains only partially identified.

The converse must also be demonstrated:

> A point estimate can exist while the defensive action remains scientifically ambiguous.

## 2.3 New contribution boundary

Novelty is attached to the cybersecurity formulation and operational coupling:

$$
\text{distributed control constraints}
\rightarrow
\mathcal G
\rightarrow
\mathcal G^{pred}
\rightarrow
[L_o,U_o]
\rightarrow
\text{certificate/ambiguity}
\rightarrow
\text{valid prospective hardening}.
$$

No novelty credit is assigned to the established mathematics used internally, including:

* fusion-frame geometry;
* projection operators;
* pseudoinverse reconstruction;
* PCA/SVD;
* subspace perturbation;
* partial identification generally;
* set-membership estimation generally;
* support-function optimization;
* functional observability;
* robust optimization;
* temporal state-space propagation;
* adversarial training;
* experimental-design criteria.

## 2.4 Explicit non-goals

FedACT does not claim:

* attacker-intent identification;
* causal identification of attacker behavior;
* prediction of discontinuous zero-days without precursor structure;
* universal malware generation;
* universal future-malware prediction;
* universal robustness;
* formal Byzantine security;
* formal privacy accounting;
* deployment readiness;
* arbitrary-organization generalization;
* nonlinear nuisance modeling as a primary contribution;
* foundational new observability or partial-identification mathematics.

Synthetic federation may establish mathematical behavior but may not establish real organizational complementarity.

---

# 3. Research Questions and Falsifiable Hypotheses

## Feasible-Set Validity

**Question:** Do distributed control constraints produce calibrated feasible transition sets under the declared uncertainty model?

### Falsifiable hypothesis

When model assumptions and declared uncertainty budgets hold, the true synthetic shared transition belongs to the FedACT feasible set at the calibrated coverage level.

**Falsification:** empirical coverage is materially below the prespecified nominal coverage after accounting for finite Monte Carlo uncertainty.

**Inconclusive:** insufficient repetitions or unresolved coverage calibration.

---

## Action Identification Without Full Transition Identification

**Question:** Can an action functional become identifiable while the full transition remains nonidentified?

### Falsifiable hypothesis

With a nontrivial global unresolved subspace, actions orthogonal or nearly orthogonal to that subspace can have narrow support intervals and become certified.

**Falsification:** action intervals remain uninformative whenever full transition identification fails.

---

## Point Prediction Versus Decision Identification

**Question:** Does explicit action uncertainty reject actions that a point estimate would incorrectly approve?

### Falsifiable hypothesis

Point-positive but FedACT-ambiguous actions have lower later-real relevance than FedACT-certified actions.

**Falsification:** point-positive ambiguous actions are statistically indistinguishable from, or superior to, certified actions in prospective relevance.

---

## Complementary Federation

**Question:** Does heterogeneous control geometry provide identification gain beyond replication gain?

### Falsifiable hypothesis

At matched total sample count and noise, complementary client geometry contracts action intervals more than redundant client geometry and converts more ambiguous actions into identified states.

**Falsification:** the advantage disappears when sample count is controlled.

---

## Action-Specific Information

**Question:** Is action-specific uncertainty more informative than global spectral identifiability for security decisions?

### Falsifiable hypothesis

At fixed global identification geometry, rotating an action direction toward unresolved dimensions increases the action interval width and changes its certification state without changing global rank.

**Falsification:** global spectral diagnostics predict action eligibility as well as direct support intervals.

---

## Prospective Action Validity

**Question:** Do FedACT certificates predict later-real action relevance?

### Falsifiable hypothesis

Across locked rolling cutoffs:

$$
\text{certified actions} >
\text{point-positive ambiguous actions} >
\text{matched random valid actions}
$$

for later-real action relevance.

This ordering is evaluated statistically across repeated cutoff units; it is not required in every individual cutoff.

---

## Prospective Hardening Benefit

**Question:** Does hardening with certified actions reduce pre-feedback defensive exposure?

### Falsifiable hypothesis

FedACT hardening improves early-horizon malicious detection or cumulative pre-adaptation exposure at a prespecified acceptable clean-data cost relative to required baselines.

**Falsification:** no material exposure reduction exists, or clean-data cost eliminates the security benefit.

---

## Graceful Failure and Abstention

**Question:** Does FedACT become uncertain in regimes where its assumptions predict non-identification?

### Falsifiable hypothesis

Increasing:

* control-span violation;
* private contamination;
* unresolved action geometry;
* forecast horizon;
* synchronized unmodeled nuisance;
* insufficient controls;

causes wider intervals, more ambiguity, or abstention rather than unjustified confidence.

---

## Temporal Contribution

**Question:** Does chronological evolution contribute information beyond static action geometry?

### Falsifiable hypothesis

Destroying historical temporal order materially weakens prospective action relevance and/or downstream hardening value.

**Falsification:** temporal shuffling yields equivalent prospective performance.

---

## Cross-Corpus Generalization

**Question:** Does the mechanism replicate on a second scientifically valid chronological corpus?

### Falsifiable hypothesis

The second corpus reproduces the qualitative mechanism:

$$
\text{control evidence}
\rightarrow
\text{action uncertainty}
\rightarrow
\text{certificate quality}
\rightarrow
\text{prospective consequence},
$$

without changing the primary estimand or certification semantics.

---

## Optional Communication-Limited Client Selection

**Question:** Under an equal communication budget, does action-focused client selection reduce relevant uncertainty more efficiently?

### Falsifiable hypothesis

Action-interval-contraction selection produces greater weighted action-width reduction per participating client than random or sample-count selection and is compared against an established global-information selector.

This hypothesis is secondary.

---

# 4. Formal Observation Model and Primary Estimands

## 4.1 Observation model

For client \(k\), cohort \(c\), historical transition endpoint \(t\):

\[
\Delta M_{k,c,t} =
g_{c,t}
+
U_{k,c,t}a_{k,c,t}
+
r_{k,c,t}
+
\ell_{k,c,t}
+
\varepsilon_{k,c,t}.
\]

Where:

* \(g_{c,t}\in\mathbb R^d\): transferable shared threat-transition component;
* \(U_{k,c,t}a_{k,c,t}\): nuisance lying in the control-estimated nuisance span;
* \(r_{k,c,t}\): nuisance outside the available control span;
* \(\ell_{k,c,t}\): client-private or targeted threat transition;
* \(\varepsilon_{k,c,t}\): sampling and representation noise.

The nuisance subspace is

\[
\mathcal N_{k,c,t}=\mathrm{col}(U_{k,c,t}).
\]

The ideal nuisance-removing projector is

\[
P_{k,c,t}=I-U_{k,c,t}U_{k,c,t}^{\top},
\]

and the estimated projector is

\[
\hat P_{k,c,t}=I-\hat U_{k,c,t}\hat U_{k,c,t}^{\top}.
\]

For any positive-semidefinite matrix \(S\), the roadmap uses

\[
\|v\|_{S^{\dagger}}=\sqrt{v^{\top}S^{\dagger}v}.
\]

## 4.2 PRIMARY ESTIMAND — control-compatible shared transition set

\[
\boxed{
\mathcal G_{c,t} =
\left\lbrace
g:
\left\|
\hat P_{k,c,t}
\left(
\Delta M_{k,c,t}-g
\right)
\right\|_{\hat\Sigma_{k,c,t}^{\dagger}}
\le
\beta_{k,c,t}
\;\forall k,
\quad
g\in\mathcal R_{c,t}
\right\rbrace.
}
\]

\(\mathcal R_{c,t}\) is the pre-cutoff historical plausibility constraint required to bound globally unresolved directions.

The primary estimand is **not** a reconstructed point \(g\).

## 4.3 Prospective feasible set

Reference temporal model:

\[
g_{t+1}=Ag_t+w_t,
\qquad
w_t\in\mathcal W.
\]

For horizon \(h\) measured in cutoff steps:

\[
\boxed{
\mathcal G^{pred}_{c,T+h} =
A^h\mathcal G_{c,T}
\oplus
\bigoplus_{j=0}^{h-1}A^j\mathcal W.
}
\]

A verified outer convex approximation may substitute for exact propagation only when its coverage behavior is validated before confirmatory experiments.

## 4.4 Valid action displacement

For cutoff-fixed encoder \(E_T\), original sample \(x\), and valid operator \(o\):

\[
q_o(x) =
\frac{
E_T(o(x))-E_T(x)
}{
\|E_T(o(x))-E_T(x)\|_2
}.
\]

If the denominator is below the numerical zero-displacement floor, the action is degenerate and must be rejected.

The evaluation unit is:

\[
(x,o,c,h).
\]

## 4.5 PRIMARY ACTION ESTIMAND

For any prospective feasible set:

\[
\psi_o(g)=q_o(x)^\top g.
\]

Its sharp support interval is

\[
\boxed{
I_o(\mathcal G) =
[L_o,U_o] =
\left[
\inf_{g\in\mathcal G}q_o^\top g,
\sup_{g\in\mathcal G}q_o^\top g
\right].
}
\]

Interval width:

\[
W_o=U_o-L_o.
\]

## 4.6 Decision states

### Positively identified

\[
L_o\ge\tau_{align}.
\]

### Negatively identified

\[
U_o<\tau_{align}.
\]

### Ambiguous

\[
L_o<\tau_{align}\le U_o.
\]

### Certified

\[
\boxed{
\mathrm{Cert}_o =
\mathbf 1
\left[
L_o\ge\tau_{align}
\land
W_o\le\tau_{amb}
\land
\mathrm{valid}(o)=1
\right].
}
\]

### Abstention

No speculative challenge is injected when no valid action is certified.

## 4.7 DIAGNOSTIC QUANTITIES

The following are diagnostic rather than primary estimands:

* the Chebyshev center \(\hat g\) of a bounded FedACT set;
* the cutoff-safe propagated point comparator \(\hat g^{pred}_{T+h}=A^h\hat g_T\);
* global frame/operator rank;
* global condition number;
* smallest positive eigenvalue;
* pairwise principal angles;
* feasible-set diameter upper bound;
* action-conditioning index;
* leave-one-client-out certificate stability.

The propagated point comparator is the authoritative point quantity used to define “point-positive” actions unless a named baseline explicitly defines a different point estimator.

## 4.8 BASELINE QUANTITIES

Point-estimate comparators may use quantities such as

\[
\hat g=H^\dagger b,
\]

or regularized/covariance-weighted variants defined in §14.

Such quantities must never replace the FedACT primary estimand.

# 5. Scientific Mechanism and Evidence Chain

The mechanism tested by the paper is:

```text
control evidence
→ client constraint quality
→ global transition-set geometry
→ action-functional uncertainty
→ certificate / ambiguity / abstention
→ later-real action relevance
→ proactive defensive consequence
```

## Controls → valid constraints

Required evidence:

* held-out control reconstruction;
* subspace stability;
* eigengap diagnostics;
* feasible-set coverage in known-truth simulation;
* sensitivity to control-span violation.

**Falsified if:** constraints systematically exclude the truth under declared assumptions.

## Constraints → transition-set geometry

Required evidence:

* width decreases with increasing valid information;
* structural unresolved directions persist despite repeated redundant data;
* complementary constraints contract different dimensions.

**Falsified if:** set behavior contradicts the underlying geometry.

## Transition set → action interval

Required evidence:

* action width changes with action orientation even when global rank is fixed;
* support solvers match analytical cases;
* interval contraction is monotone under added constraints.

**Falsified if:** action intervals do not reflect the geometry of the compatible set.

## Action interval → certification quality

Required evidence:

* certified actions predict later-real alignment;
* ambiguous point-positive actions are less reliable;
* matched random valid actions are less relevant.

**Falsified if:** certification carries no prospective information.

## Certificate → security consequence

Required evidence:

* hardening uses only certified, valid actions;
* augmentation count and validity are matched against baselines;
* early exposure improves at acceptable clean cost.

**Falsified if:** equivalent benefit is reproduced by matched generic augmentation/uncertainty.

## Failure boundary → abstention

Required evidence:

* increased irreducible ambiguity widens intervals;
* certification rate falls appropriately;
* synchronized unmodeled nuisance is not falsely resolved.

**Falsified if:** confidence remains high despite known non-identification.

---

# 6. Assumption and Validity Contract

| Assumption                   | Statement                                                                         | Mathematical role                         | Operationalization                     | Test/diagnostic                         | Failure consequence                                          |
| ---------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------- | -------------------------------------- | --------------------------------------- | ------------------------------------------------------------ |
| Chronology                   | Every scientific decision uses information available by cutoff \(T\)                | Valid prospective interpretation          | cutoff manifests                       | leakage audit                           | prospective claims invalid                                   |
| Shared component             | A meaningful shared component \(g_{c,t}\) exists for some cohorts/windows           | Defines global estimand                   | cross-client feasibility and stability | local-vs-global diagnostics             | global interpretation unsupported                            |
| Informative controls         | Benign/control transitions reveal part of nuisance geometry                       | Makes projection constraints meaningful   | matched control strata                 | held-out control reconstruction         | control-based identification unsupported                     |
| Control-span validity        | \(|P_kr_k|\le\rho_k\) under declared sensitivity level                              | Bounds residual nuisance                  | calibrated/sensitivity radius          | violation sweeps                        | coverage/certificates invalid if understated                 |
| Private-transition allowance | \(|P_k\ell_k|\le\xi_k\) or robust formulation tolerates private modes               | Protects shared-transition inference      | calibrated/sensitivity allowance       | private-transition sweep                | global certificates may be false                             |
| Cutoff-fixed representation  | Representation remains fixed within each cutoff experiment                        | Preserves transition geometry             | encoder hash lock                      | artifact verification                   | mechanistic attribution invalid                              |
| Action validity              | Every candidate operator preserves the domain validity contract                   | Gives security semantics                  | operator-specific validator            | validity audit                          | certified transformation unusable                            |
| Historical predictability    | Historical action support contains predictive information for later horizons      | Required for prospective claims           | nested pseudo-future calibration       | time shuffle and pseudo-future coverage | prospective claim unsupported                                |
| Eigendecomposition stability | Selected nuisance subspace is statistically stable                                | Finite-sample subspace bound              | minimum eigengap criterion             | bootstrap/stability diagnostic          | client constraint unusable                                   |
| Minimum support              | Sufficient malicious and control support exists                                   | Controls estimation error                 | minimum-support gate                   | support counts                          | cohort/client excluded                                       |
| Plausibility-set coverage    | Historical plausibility set contains the true transition with calibrated behavior | Bounds structurally unresolved dimensions | pre-cutoff calibration                 | radius sensitivity                      | certificates may be prior-dominated                          |
| Honest primary federation    | Primary federation consists of authenticated, non-Byzantine organizations         | Bounds threat model                       | provenance/authentication              | outlier stress tests only               | Byzantine-security claims prohibited                         |
| Operator coverage            | Valid operator library contains meaningful challenge directions                   | Gives downstream actionability            | operator coverage audit                | later-real coverage diagnostics         | mechanism may be statistically valid but operationally empty |
| Temporal stability           | Chosen low-capacity temporal dynamics are usable over the prospective horizon     | Enables set propagation                   | nested pseudo-future validation        | horizon calibration                     | long-horizon certification must abstain                      |

## 6.1 Fundamental non-identification condition

If a component \(s\neq0\):

1. is shared across clients;
2. lies outside every control nuisance span;
3. has no independent control signature;

then observations cannot distinguish (g+s) from the true threat component.

FedACT must not claim that federation resolves this case.

## 6.2 Tail-behavior condition

The primary finite-sample construction uses empirical, cutoff-safe bootstrap calibration and does not require an unverified Gaussian covariance formula.

For every eligible client/window, after scale standardization and nuisance projection, compute coordinate-wise excess kurtosis on the observations used by the corresponding uncertainty estimator. A client/window is **tail-flagged** when more than `identification.tail_diagnostic.maximum_flagged_coordinate_fraction` of finite projected coordinates have absolute excess kurtosis above `identification.tail_diagnostic.maximum_absolute_excess_kurtosis`.

Tail flagging is diagnostic for the primary estimator. A prespecified robust sensitivity is additionally computed with:

* coordinate-wise median centering for mean diagnostics;
* Minimum Covariance Determinant covariance when the number of observations exceeds the embedding dimension and the estimator is numerically defined;
* the same empirical bootstrap quantile construction used by the primary uncertainty estimator.

The robust sensitivity may not silently replace the primary confirmatory estimator. If a primary confirmatory conclusion materially depends on a tail-flagged client/window and the robust sensitivity changes the corresponding certificate or primary endpoint conclusion, that unit is classified `ASSUMPTION_VIOLATION` and may not support the affected claim.

# 7. Theoretical Result and Proof-Obligation Program

## Theoretical results and proof obligations

### Exact population identified set

**Class:** KNOWN MATHEMATICS.

With exact constraints

\[
y_k=g+n_k,\qquad n_k\in\mathcal N_k,
\]

define

\[
A=
\begin{bmatrix}
\sqrt{w_1}P_1\\
\vdots\\
\sqrt{w_K}P_K
\end{bmatrix},
\qquad
b=
\begin{bmatrix}
\sqrt{w_1}P_1y_1\\
\vdots\\
\sqrt{w_K}P_Ky_K
\end{bmatrix}.
\]

If \(g_0\) is one exact solution, then

\[
\boxed{
\mathcal G^* =
g_0+\ker(A) =
g_0+\bigcap_k\mathcal N_k.
}
\]

**Proof obligation:** reproduce a concise self-contained derivation while citing the classical projection/fusion-frame lineage.

**Verification:** analytically solvable toy systems.

### Functional identifiability

**Class:** KNOWN MATHEMATICS / ADAPTED RESULT.

For \(\psi_q(g)=q^\top g\),

\[
\psi_q(g)\text{ is point identified}
\iff
q\perp\ker(A)
\iff
q\in\mathrm{range}(A^\top).
\]

**FedACT-specific consequence:** action identity may be resolved while full transition identity is not.

**Verification:** Action-Specific versus Global Identification.

### Action-specific conditioning bound

**Class:** ADAPTED RESULT.

For

\[
\mathcal G_\epsilon =
\lbrace g:\|Ag-b\|_2\le\epsilon\rbrace
\]

and \(q\in\mathrm{range}(A^\top)\),

\[
\boxed{
W_q(\mathcal G_\epsilon)
\le
2\epsilon\sqrt{q^\top H^\dagger q},
\qquad
H=A^\top A.
}
\]

Define the diagnostic

\[
\kappa_{act}(q;H)=\sqrt{q^\top H^\dagger q}.
\]

**Verification:** spectral-conditioning sweeps.

### Irreducible action ambiguity

**Class:** ADAPTED RESULT.

If an action has a component in \(\ker(H)\), observations alone cannot identify that component. With a symmetric plausibility ball of radius \(R\), the unresolved contribution is controlled by

\[
\|P_{\ker(H)}q\|_2
\]

and contributes exactly \(2R\|P_{\ker(H)}q\|_2\) when the unresolved component can vary independently over that ball.

**Empirical consequence:** report radius dependence whenever certification is materially influenced by unresolved directions.

### Approximate control-span validity

**Class:** ADAPTED RESULT.

Assuming

\[
\|P_kr_k\|_2\le\rho_{k,2},\qquad
\|P_k\ell_k\|_2\le\xi_{k,2},
\]

and an empirically calibrated sampling/subspace error event, the corresponding standardized client residual is bounded by the sum of the calibrated standardized contributions used in §8.2.

The execution contract does not introduce unknown multiplicative constants such as \(c_M\) or \(c_U\). All finite-sample uncertainty components are computed by the explicit empirical bootstrap and residual-quantile procedures in §8.2.

### Estimated nuisance subspaces

**Class:** KNOWN MATHEMATICS / ADAPTED APPLICATION.

Let \(\lambda_{1,k}\ge\cdots\ge\lambda_{d,k}\ge0\) be eigenvalues of the unregularized weighted control-transition covariance. For candidate rank \(r\), define the executable eigengap ratio

\[
\Gamma_{k,r} =
\frac{\lambda_{r,k}}
{\max\lbrace\lambda_{r+1,k},
\epsilon_{\mathrm{rank}}\lambda_{1,k},
\epsilon_{\mathrm{scale}}\rbrace},
\]

where \(\epsilon_{\mathrm{rank}}\) and \(\epsilon_{\mathrm{scale}}\) are the numerical configuration values.

Standard subspace perturbation theory implies schematically

\[
\|\hat P_k-P_k\|_2
\lesssim
\frac{\|\hat C_k^B-C_k^B\|_2}
{\lambda_{r,k}-\lambda_{r+1,k}}
\]

when the eigengap is positive. FedACT operationalizes this uncertainty directly through bootstrap projector perturbations rather than an unspecified analytical constant.

### Feasible-set coverage

**Class:** ADAPTED RESULT.

For each client \(k\), let the sampling, subspace, control-span, and private-transition events be calibrated with simultaneous error allocation as defined in §8.2. If all client events hold and the historical plausibility set contains the truth, then

\[
\Pr[g\in\hat{\mathcal G}]
\ge 1-\delta
\]

under the bootstrap-consistency and residual-exchangeability conditions stated by the implemented estimators.

**Proof obligation:** state the regularity conditions needed for the empirical bootstrap and residual quantiles, prove the union-bound allocation over usable clients, and verify the resulting coverage in known-truth simulation. No theorem may rely on a constant or estimator that is absent from the executable algorithm.

### Finite-sample action width

**Class:** ADAPTED RESULT.

For an identifiable action direction, finite-sample width contracts as the standardized client radii contract, subject to the structural contribution of the plausibility set. In the single stacked-ellipsoid reference case,

\[
W_q(\hat{\mathcal G})
\lesssim
2\epsilon_{\mathrm{eff}}
\sqrt{q^\top\hat H^\dagger q}
+
\mathcal E_{\mathrm{radius}}(q).
\]

**Prediction:** increasing control and malicious support reduces reducible uncertainty until structural or declared contamination terms dominate.

### Constraint monotonicity

**Class:** KNOWN MATHEMATICS.

For

\[
\mathcal G^+=\mathcal G\cap\mathcal C_j,
\]

\[
L_o(\mathcal G^+)\ge L_o(\mathcal G),
\qquad
U_o(\mathcal G^+)\le U_o(\mathcal G).
\]

**FedACT-specific consequence:** a new valid control view can convert an ambiguous action into an identified action.

### Redundancy versus complementarity

**Class:** KNOWN GEOMETRY / FedACT-specific scientific consequence.

Repeated equivalent projectors reduce finite-sample uncertainty but do not remove their exact common nullspace. Complementary projectors can remove action-relevant unresolved directions.

**Mandatory verification:** equal-total-sample redundant versus complementary experiment.

### Synchronized residual non-identification

**Class:** ADAPTED IMPOSSIBILITY RESULT.

If

\[
y_k=g+s+U_ka_k+e_k
\]

for every client and \(s\) has no independent control signature, the decomposition of \(g+s\) into shared threat versus shared residual nuisance is not identifiable from the permitted observations.

**Mandatory verification:** synchronized-residual synthetic experiment.

### Identifiable-functional contraction

**Class:** ADAPTED RESULT.

Under:

1. \(n_k^B,n_k^M\rightarrow\infty\);
2. eigengaps bounded away from zero;
3. \(\hat P_k\rightarrow P_k\);
4. sampling error vanishes;
5. \(\rho_k,\xi_k\rightarrow0\) in the ideal regime;
6. the plausibility set contains the truth;
7. \(q\in\mathrm{range}(A^\top)\);

the action interval contracts to a singleton.

Full transition contraction additionally requires

\[
\bigcap_k\mathcal N_k=\lbrace0\rbrace.
\]

# 8. FedACT Algorithm Contract

## 8.1 Client inputs

For client \(k\), cohort \(c\), transition endpoint \(t\), and external cutoff \(T\), the client receives only data permitted by §9:

### Malicious observations

\[
D^M_k=\lbrace(x_i,t_i,c_i,u_i)\rbrace.
\]

### Benign/control observations

\[
D^B_k=\lbrace(x_j,t_j,u_j,s_j)\rbrace.
\]

### Cutoff-fixed representation

\[
E_T:x\mapsto z\in\mathbb R^d.
\]

### Detector

\[
f_\phi=h_\phi\circ E_T.
\]

### Valid operator library

\[
\mathcal O_T(x).
\]

### Calibrated configuration

Includes the configuration values and derived quantities required by this section, including support, nuisance-rank/eigengap criteria, uncertainty coverage, residual allowances, historical plausibility radius, temporal model, action thresholds, operator coverage, and hardening policy.

## 8.2 Client procedure

### Cutoff-safe malicious transition

Let \(\Delta=\texttt{temporal.transition＿interval＿months}\). For every eligible transition endpoint \(t\), use the two adjacent half-open windows defined in §9.3:

\[
W_t^-=[t-2\Delta,t-\Delta),
\qquad
W_t^+=[t-\Delta,t).
\]

For cohort \(c\),

\[
\hat\mu^{M,-}_{k,c,t} =
\frac1{n^{M,-}_{k,c,t}}
\sum_{i\in M(k,c,W_t^-)}E_T(x_i),
\]

\[
\hat\mu^{M,+}_{k,c,t} =
\frac1{n^{M,+}_{k,c,t}}
\sum_{i\in M(k,c,W_t^+)}E_T(x_i),
\]

and

\[
y_{k,c,t} =
\hat\mu^{M,+}_{k,c,t} -
\hat\mu^{M,-}_{k,c,t}.
\]

Both malicious sides must independently satisfy `identification.minimum_support_per_class`.

### Matched control-transition replicates

A control-transition replicate is a distinct eligible historical/context cell \(s\), never an arbitrary random shard. For the same adjacent windows,

\[
b^{(s)}_{k,c,t} =
\hat\mu^{B,s,+}_{k,c,t} -
\hat\mu^{B,s,-}_{k,c,t}.
\]

Let \(n_s^-\) and \(n_s^+\) be the benign counts forming replicate \(s\). Define its effective support

\[
m_s =
\left(\frac1{n_s^-}+\frac1{n_s^+}\right)^{-1},
\qquad
\omega_s=\frac{m_s}{\sum_jm_j}.
\]

At least `identification.minimum_control_transition_replicates` finite control-transition replicates are required after dataset-specific matching. Otherwise the client is unusable for identification and emits `ABSTAIN_NO_USABLE_CONTROL`.

### Nuisance covariance and rank

Define

\[
\bar b=\sum_s\omega_sb^{(s)}
\]

and the unregularized weighted covariance

\[
\hat C^B_{\mathrm{raw}} =
\sum_s\omega_s
(b^{(s)}-\bar b)(b^{(s)}-\bar b)^\top.
\]

Let its eigenvalues be

\[
\lambda_1\ge\lambda_2\ge\cdots\ge\lambda_d\ge0.
\]

The admissible candidate ranks are the configured candidates not exceeding

\[
r_{\max}^{\mathrm{data}} =
\min\lbrace
d-1,\;
S-1,\;
\texttt{identification.nuisance＿rank.maximum}
\rbrace,
\]

where \(S\) is the number of control-transition replicates.

For each admissible rank \(r\), compute

\[
\Gamma_r =
\frac{\lambda_r}
{\max\lbrace
\lambda_{r+1},
\texttt{numerical.rank＿clip＿epsilon＿relative}\lambda_1,
\texttt{numerical.scale＿standardization＿floor}
\rbrace}.
\]

The selected rank is the largest admissible \(r\) whose ratio meets the calibrated eigengap requirement. If none qualifies, the client emits `ABSTAIN_WEAK_EIGENGAP`.

Rank stability is evaluated by a weighted nonparametric bootstrap of the \(S\) control-transition replicates using `identification.nuisance_rank.bootstrap_resamples` resamples and the `seeds.calibration` stream. The selected rank must equal the full-sample selected rank in at least `identification.nuisance_rank.minimum_bootstrap_stability_fraction` of resamples. Otherwise the client emits `ABSTAIN_UNSTABLE_NUISANCE_RANK`.

Define the regularized nuisance covariance

\[
\hat C^B =
\hat C^B_{\mathrm{raw}}+\eta I,
\]

\[
\eta =
\max\left\lbrace
\texttt{numerical.scale＿standardization＿floor},
\;
c\frac{\mathrm{tr}(\hat C^B_{\mathrm{raw}})}d
\right\rbrace,
\]

where \(c\) is the selected value from `identification.covariance_regularization`.

Let \(\hat U_k\) contain the leading \(r_k\) eigenvectors of \(\hat C^B_{\mathrm{raw}}\) and define

\[
\hat P_k=I-\hat U_k\hat U_k^\top.
\]

### Malicious-transition covariance

Let \(\hat S^{M,-}\) and \(\hat S^{M,+}\) be unbiased sample covariance matrices of the cutoff-fixed embeddings in \(W_t^-\) and \(W_t^+\). Define the covariance of the mean displacement

\[
\hat V^M =
\frac{\hat S^{M,-}}{n^{M,-}}
+
\frac{\hat S^{M,+}}{n^{M,+}},
\]

\[
\hat\Sigma_{\mathrm{raw}} =
\hat P_k\hat V^M\hat P_k,
\]

and

\[
\hat\Sigma_k =
\hat\Sigma_{\mathrm{raw}}+\zeta I,
\]

\[
\zeta =
\max\left\lbrace
\texttt{numerical.scale＿standardization＿floor},
\;
c\frac{\mathrm{tr}(\hat V^M)}d
\right\rbrace.
\]

The same selected covariance-regularization coefficient \(c\) is used for \(\hat C^B\) and \(\hat\Sigma_k\). Every inverse norm in FedACT uses the positive-definite \(\hat\Sigma_k^{-1}\); a pseudoinverse is used only in explicitly named point-estimator diagnostics.

### Constraint uncertainty

Let \(p\) be the selected target coverage and \(K\) the number of currently quality-eligible clients for the cohort/window before uncertainty gates. Allocate

\[
\alpha_M=\alpha_U=\frac{1-p}{2K}.
\]

All bootstrap quantiles use linear interpolation as defined in §17.

#### Malicious sampling term

Resample malicious observations independently within \(W_t^-\) and \(W_t^+\), preserving their observed counts, using `identification.uncertainty.bootstrap_resamples` draws from the `seeds.calibration` stream. For draw \(b\), compute \(y_k^{*(b)}\). Define

\[
s^M_k =
Q_{1-\alpha_M}
\left(
\left\|
\hat P_k(y_k^{*(b)}-y_k)
\right\|_{\hat\Sigma_k^{-1}}
\right).
\]

#### Subspace-estimation term

Using the control-transition bootstrap described above, recompute \(\hat P_k^{*(b)}\) at the selected rank and define

\[
e^U_k =
Q_{1-\alpha_U}
\left(
\|\hat P_k^{*(b)}-\hat P_k\|_2
\right).
\]

Define the observed nuisance-amplitude bound

\[
A_k =
Q_{0.95}
\left(
\lbrace\|b^{(s)}-\bar b\|_2\rbrace
\right).
\]

Convert projector perturbation to the standardized residual scale by

\[
u^U_k =
\frac{
e^U_k A_k
}{
\sqrt{\lambda_{\min}(\hat\Sigma_k)}
}.
\]

This term depends only on observed control-transition amplitude and is therefore available before historical plausibility-set construction.

#### Control-span violation allowance

For each control-transition replicate \(s\), fit the nuisance subspace without that replicate and compute its Euclidean held-out reconstruction residual

\[
d_{\rho,s} =
\left\|
\hat P_{k,-s}
\left(b^{(s)}-\bar b_{-s}\right)
\right\|_2.
\]

Let

\[
\rho_{k,2} =
Q_{1-\alpha_\rho}(\lbrace d_{\rho,s}\rbrace),
\]

where \(\alpha_\rho\) is selected from `identification.control_span_violation`. Convert it to the standardized client norm:

\[
\rho_k =
\frac{\rho_{k,2}}
{\sqrt{\lambda_{\min}(\hat\Sigma_k)}}.
\]

#### Private-transition allowance

When at least two quality-eligible clients exist for the same cohort/window, define the leave-one-client reference

\[
m_{-k} =
\mathrm{GeoMedian}
\left(
\lbrace
\hat P_jy_j:j\ne k
\rbrace
\right)
\]

and collect, over eligible pre-cutoff transition endpoints, the historical residuals

\[
d_{\xi,k,t} =
\|\hat P_ky_{k,t}-m_{-k,t}\|_2.
\]

When only one client exists, use leave-one-transition-out residuals of the geometric median of the client's other strictly earlier projected malicious transitions as the conservative private-transition proxy; this uses no feasible-set center or temporal-model output. At least `identification.private_contamination.minimum_history_residuals` historical residuals are required. Otherwise the unit emits `ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY`.

Define

\[
\xi_{k,2} =
Q_{1-\alpha_\xi}(\lbrace d_{\xi,k,t}\rbrace),
\qquad
\xi_k =
\frac{\xi_{k,2}}
{\sqrt{\lambda_{\min}(\hat\Sigma_k)}},
\]

where \(\alpha_\xi\) is selected from `identification.private_contamination`.

#### Final client radius

The executable standardized client radius is

\[
\boxed{
\beta_k =
s^M_k+u^U_k+\rho_k+\xi_k.
}
\]

No unresolved analytical multiplier is introduced by implementation.

### Client quality gate

A client is usable for identification only if all of the following hold:

1. both malicious transition sides satisfy the minimum support;
2. both sides of every used control replicate satisfy the control support floor;
3. at least the minimum number of control-transition replicates exists;
4. the selected nuisance rank passes the eigengap and bootstrap-stability rules;
5. \(\hat\Sigma_k\), all uncertainty terms, and \(\beta_k\) are finite;
6. \(\lambda_{\min}(\hat\Sigma_k)>0\);
7. the private-transition history requirement is met;
8. held-out control reconstruction passes the following fixed gate.

For the held-out control gate, compute the in-sample nuisance-reconstruction residual distribution and its configured quantile threshold. The fraction of leave-one-replicate residuals not exceeding that threshold must be at least `identification.control_reconstruction_gate.minimum_pass_fraction`. Otherwise emit `ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE`.

Leave-one-client-out certificate stability is not a client admissibility gate; it is evaluated after certificate construction as specified in §8.3.

### Transmission

Transmit

\[
(
\hat U_k,
y_k,
\hat\Sigma_k,
n_k^{M,-},
n_k^{M,+},
n_k^B,
\hat\gamma_k,
\hat\beta_k,
d_k^{control}
).
\]

A dense projector is not transmitted.

## 8.3 Server procedure

### Validate client constraints

Reject from identification every client/cohort/window failing the locked client-quality gate in §8.2. A federation result requires at least two usable clients; a single usable client may still support local action-mechanism evidence.

### Construct the historical plausibility radius without circularity

Before imposing an L2 plausibility ball, solve the **minimum-norm control-compatible point**

\[
\tilde g_{c,t} =
\arg\min_g \|g\|_2
\]

subject to the per-client standardized residual constraints at historical transition endpoint \(t\). This optimization contains no historical plausibility-radius constraint.

For the current cohort family, collect \(\|\tilde g_{c,u}\|_2\) from strictly earlier eligible pre-cutoff endpoints \(u<t\). At least `identification.historical_plausibility_radius.minimum_reference_centers` reference centers are required. Define

\[
R^{base}_{c,t} =
Q_{\texttt{identification.historical＿plausibility＿radius.center＿norm＿quantile}}
\left(
\lbrace\|\tilde g_{c,u}\|_2:u<t\rbrace
\right).
\]

The primary radius is \(R_{c,t}=R^{base}_{c,t}\); sensitivity analyses multiply this base radius by the configured sensitivity multipliers. When the minimum reference history does not exist, the unit is `INSUFFICIENT_EVIDENCE` and no radius is invented.

### Construct historical feasible set

\[
\boxed{
\mathcal G_{c,t} =
\lbrace g:\|g\|_2\le R_{c,t}\rbrace
\cap
\bigcap_{k\in\mathcal K_{c,t}}
\left\lbrace
g:
\|
\hat P_{k,c,t}(y_{k,c,t}-g)
\|_{\hat\Sigma_{k,c,t}^{-1}}
\le
\beta_{k,c,t}
\right\rbrace.
}
\]

### Handle infeasibility

Never silently enlarge constraints.

If \(\mathcal G_{c,t}=\varnothing\), the scientific outcome is `INFEASIBLE`. The executor computes the minimum uniform inflation factor \(\kappa\ge1\) applied to all client radii that would make the intersection nonempty and reports \(\kappa\) only as a feasibility-violation diagnostic. The analysis-facing feasible set is not replaced by the inflated diagnostic set.

The diagnostic records whether the failure is associated with uncertainty underestimation, an explicit sensitivity condition, or model/control failure. Confirmatory missingness is classified `SCIENTIFIC_INFEASIBILITY`.

### Feasible-set center

The temporal state representative \(\hat g_{c,t}\) is the Euclidean Chebyshev center of \(\mathcal G_{c,t}\): the center of the largest Euclidean ball contained in the convex set. It is obtained by the second-order-cone formulation implemented by the support/feasibility solver. If the maximal radius has multiple centers within `numerical.projection_tie_tolerance`, choose the minimum-L2-norm center. This definition is used consistently for temporal fitting, diagnostics, and provenance.

### Fit temporal set model

The low-capacity temporal family is restricted to an isotropic scalar transition:

\[
g_{t+1}=a g_t+w_t,\qquad A=aI,\qquad w_t\in\mathcal W.
\]

The step of this model is exactly `temporal.cutoff_step_months`. For consecutive eligible pre-cutoff centers \((\hat g_u,\hat g_{u+1})\), fit

\[
a_{\mathrm{raw}} =
\frac{\sum_u\hat g_u^\top\hat g_{u+1}}
{\sum_u\|\hat g_u\|_2^2}.
\]

If the denominator is at or below `numerical.scale_standardization_floor`, set \(a=1\). Otherwise set

\[
a=\min\lbrace
\texttt{temporal.temporal＿model.maximum＿scalar＿coefficient},
\max\lbrace0,a_{\mathrm{raw}}\rbrace
\rbrace.
\]

At least `temporal.temporal_model.minimum_consecutive_pairs` valid consecutive center pairs are required; otherwise the prospective unit is `INSUFFICIENT_EVIDENCE`.

Define one-step residuals

\[
e_u=\hat g_{u+1}-a\hat g_u
\]

and let the process-error set be the L2 ball

\[
\mathcal W =
\lbrace w:\|w\|_2\le R_W\rbrace,
\qquad
R_W =
Q_{\texttt{temporal.process＿noise.quantile}}
(\lbrace\|e_u\|_2\rbrace).
\]

Thus the process-error radius is calibrated from temporal-model residuals, not raw center displacements.

### Propagate

For a forecast horizon \(h\) months, require \(h\) to be an integer multiple of `temporal.cutoff_step_months` and let \(n_h=h/\texttt{temporal.cutoff＿step＿months}\). Then

\[
\mathcal G^{pred}_{c,T+h} =
a^{n_h}\mathcal G_{c,T}
\oplus
\bigoplus_{j=0}^{n_h-1}a^j\mathcal W.
\]

Because \(a\ge0\) and \(\mathcal W\) is an L2 ball, the accumulated process component is exactly an L2 ball with radius

\[
R_W\sum_{j=0}^{n_h-1}a^j.
\]

No additional outer approximation is used by the reference implementation.

### Solve action support bounds

For every domain-valid nondegenerate \((x,o)\),

\[
L_o=\min_{g\in\mathcal G}q_o^\top g,
\qquad
U_o=\max_{g\in\mathcal G}q_o^\top g.
\]

Point reconstruction is not required.

### Deterministic prospective-set diameter bound

The abstention gate uses one fixed computable upper bound rather than an unspecified proxy. For each coordinate \(j=1,\ldots,d\), solve

\[
l_j=\min_{g\in\mathcal G}e_j^\top g,
\qquad
u_j=\max_{g\in\mathcal G}e_j^\top g.
\]

Define

\[
D_{\mathrm{box}}(\mathcal G) =
\sqrt{\sum_{j=1}^d(u_j-l_j)^2}.
\]

This is an upper bound on the Euclidean diameter of \(\mathcal G\). The same quantity is used for calibration, execution, sensitivity analysis, and reporting wherever the roadmap refers to prospective-set diameter.

### Certify

\[
\mathrm{Cert}_{o,c,h}=1
\iff
L_{o,c,h}\ge\tau_{align}
\land
U_{o,c,h}-L_{o,c,h}\le\tau_{amb}
\land
\mathrm{valid}(o)=1.
\]

The alignment and ambiguity thresholds are selected only by §25.

If \(D_{\mathrm{box}}(\mathcal G^{pred})\) exceeds the configured historical quantile, the action is not certified and the unit emits `ABSTAIN_FORECAST_SET_TOO_WIDE`.

When \(K\ge2\), leave-one-client-out stability is evaluated by reconstructing the feasible set and certificate decision after removing each usable client. The required number of unchanged decisions is

\[
\left\lceil
\texttt{certification.leave＿one＿client＿out＿stability.minimum＿unchanged＿fraction}
\times K
\right\rceil.
\]

A failing action is downgraded to `ambiguous` with `ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE`. For \(K=1\), this diagnostic is `NOT_APPLICABLE_SINGLE_CLIENT`; it does not force rejection, but no federation claim is allowed.

### Challenge set

\[
\mathcal C^{FedACT}_{c,h}(x) =
\lbrace
o(x):
o\in\mathcal O_T(x),
\mathrm{Cert}_{o,c,h}=1
\rbrace.
\]

When more actions are certified than the configured per-sample cap, always include the certified action having the lowest current-detector malicious probability, because it is the hardest currently detected challenge. Fill remaining slots greedily by maximum minimum cosine distance from already selected \(q_o\) directions. Resolve exact ties lexicographically by `(operator_name, canonical_parameter_string, output_hash)`.

### Harden

The encoder remains cutoff-fixed. Only the detector head is optimized.

Let \(L_{\mathrm{hist}}(\phi)\) be the mean unweighted binary cross-entropy-with-logits loss over the cutoff-safe historical training population, using the same benign/malicious labels as the base detector. Every generated challenge derived from a malicious source sample retains malicious target \(y=1\).

For a configured hardening weight \(\lambda\),

\[
\phi^* =
\arg\min_\phi
\left[
L_{\mathrm{hist}}(\phi)
+
\lambda
\,
\mathbb E_{x\in M_{\mathrm{hist}}}
\left(
\max_{x'\in\mathcal C^{FedACT}_{c,h}(x)}
\mathrm{BCEWithLogits}(h_\phi(E_T(x')),1)
\right)
\right].
\]

A malicious sample with an empty challenge set contributes only through \(L_{\mathrm{hist}}\); no substitute challenge is generated.

Hardening starts from the corresponding base-detector head and uses the same Adam optimizer, cosine schedule, batch size, maximum epochs, and early-stopping patience as §11. In each minibatch, at most the configured number of selected challenges per source sample is materialized; the displayed max is taken over those selected challenges. The validation objective is the same combined loss on the cutoff-safe validation partition. A checkpoint is eligible only if its clean validation FNR degradation does not exceed the configured maximum. Select the eligible epoch with the smallest combined validation objective; ties go to the earlier epoch. If no epoch, including the initialization, satisfies the clean-cost constraint, that hardening candidate is invalid.

## 8.4 Required outputs

For each valid execution unit produce:

* nuisance bases and rank/eigengap diagnostics;
* covariance and uncertainty components;
* control-quality diagnostics;
* historical minimum-norm reference centers and plausibility radii;
* historical feasible sets and centers;
* temporal-model coefficient and process-error set;
* prospective feasible sets and diameter bounds;
* action intervals;
* action states;
* abstention reasons;
* hardened detector checkpoint where applicable;
* complete provenance.

## 8.5 Abstention reason codes

```text
ABSTAIN_NO_USABLE_CONTROL
ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT
ABSTAIN_INSUFFICIENT_CONTROL_SUPPORT
ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY
ABSTAIN_UNSTABLE_NUISANCE_RANK
ABSTAIN_WEAK_EIGENGAP
ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE
ABSTAIN_FEASIBLE_SET_INCONSISTENT
ABSTAIN_INSUFFICIENT_TEMPORAL_HISTORY
ABSTAIN_FORECAST_SET_TOO_WIDE
ABSTAIN_NO_CERTIFIED_ACTION
ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT
ABSTAIN_SYNCHRONIZED_NUISANCE_RISK
ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE
```

# 9. Chronological Information Boundary

## 9.1 Cutoff rule

For every rolling external cutoff \(T_j\), a scientific input is permitted only when its source observation and every annotation used by the algorithm were available strictly before the corresponding prospective interval begins.

No information first available at or after \(T_j\) may influence:

* feature fitting or representation training;
* hyperparameter calibration;
* client/cohort definition;
* operator construction or selection;
* action selection;
* hardening;
* baseline selection or tuning.

Later-real observations are evaluation-only.

## 9.2 Information boundaries

### Representation boundary

The encoder associated with cutoff \(T_j\) is trained only from cutoff-safe data and remains immutable throughout nuisance estimation, transition construction, calibration, set construction, action-displacement construction, hardening, and corresponding later-real evaluation.

### Malicious-history boundary

Only malicious observations and labels available before \(T_j\) may contribute to historical transitions, cohorts, temporal dynamics, and calibration.

### Control-history boundary

Only benign/control observations and matching attributes available before \(T_j\) may contribute to control construction, nuisance covariance/rank estimation, and uncertainty estimation.

### Cohort boundary

Operational cohorts may use only family/context attributes that were available at the historical observation time or by the relevant cutoff. A later retrospective family annotation may be used only in an explicitly diagnostic analysis and may not define a confirmatory operational cohort.

### Calibration boundary

Every inner calibration evaluation is fully contained before its external cutoff as specified in §25.

### Operator-library boundary

Operator families, parameter grids, construction code, and validity rules are selected without inspection of later-real outcomes. An operator executable or validator version used by a cutoff is identified in provenance before evaluating that cutoff.

### Hardening boundary

The hardened detector for \(T_j\) is completed before the evaluation layer reads observations from \([T_j,T_j+h)\).

### Evaluation boundary

Later-real data are read only by evaluation producers after all corresponding scientific inputs and decision artifacts have reached `COMPLETE`.

## 9.3 Exact temporal windows

All study intervals are half-open. Let

\[
H=\texttt{temporal.historical＿training＿window＿months},
\qquad
\Delta=\texttt{temporal.transition＿interval＿months},
\qquad
s=\texttt{temporal.cutoff＿step＿months}.
\]

For historical transition endpoint \(t\),

\[
W_t^-=[t-2\Delta,t-\Delta),
\qquad
W_t^+=[t-\Delta,t).
\]

An endpoint is eligible for an external cutoff \(T\) only when both windows lie wholly inside

\[
[T-H,T).
\]

Historical transition endpoints are enumerated at step \(s\) from the source chronology. Intervals may not bridge a documented source gap; for LAMDA, the documented absence of 2015 is a hard chronology break.

For forecast horizon \(h\), the later-real evaluation interval is exactly

\[
[T,T+h).
\]

A horizon is evaluated only if that complete interval is observable in the acquired corpus. The interval is never shortened to recover an otherwise unavailable endpoint.

## 9.4 Rolling-cutoff construction

For each acquired real corpus:

1. normalize the authoritative chronology to calendar-month boundaries for study scheduling while preserving the raw source timestamp/month/week field in provenance;
2. enumerate candidate cutoffs in ascending chronological order at `temporal.cutoff_step_months`;
3. retain a cutoff only when the full historical interval \([T-H,T)\) is source-observable without crossing a prohibited gap;
4. require the complete `temporal.primary_confirmatory_horizon_months` interval for a cutoff to enter primary confirmatory analysis;
5. evaluate each other configured horizon only when its full later-real interval exists;
6. classify an unavailable requested horizon as `MISSING_SOURCE_DATA`; do not shorten it;
7. apply cohort/client/support eligibility only after these temporal conditions.

The first and last eligible cutoffs are therefore derived deterministically from the acquired release rather than hardcoded. They are recorded in the cutoff manifest.

If a dataset yields fewer than `statistics.minimum_paired_cutoffs` eligible paired confirmatory cutoffs after all predeclared eligibility rules, the workflow may execute descriptively but its affected confirmatory claim is `INSUFFICIENT_EVIDENCE`.

## 9.5 Model-retraining cadence

The representation and base detector are fully retrained every `temporal.full_retraining_interval_months`. Intermediate monthly cutoffs reuse the most recent compatible cutoff-safe representation and detector. A later retraining point may never alter an earlier cutoff result.

## 9.6 Leakage prohibitions

The following are invalid:

* normalization or feature selection using future statistics;
* representation training using later-real observations;
* operator design using future malware examples;
* future-label-informed cohort creation;
* selecting favorable cutoffs after outcome inspection;
* tuning uncertainty to improve external test coverage;
* changing action thresholds after prospective outcomes;
* tuning a baseline on information unavailable to that baseline at its corresponding operational time.

# 10. Dataset, Cohort, Client, and Control Specification

## 10.1 Dataset authority and raw-data adaptation rule

Published documentation determines the expected source semantics; the acquired raw/released files determine the executable observed schema. Every dataset loader must first inventory the acquired data and emit a schema/chronology manifest before any scientific transformation.

Documented counts, dimensions, field names, class fractions, timestamps, family labels, and client identities are validation expectations, not values to manufacture. If the acquired release differs:

1. record the observed value and source checksum;
2. map an equivalent source field only when its semantics are verified from the pinned release;
3. adapt deterministic parsing/preprocessing to the observed schema without changing the scientific estimand;
4. never synthesize a missing timestamp, family, client identity, raw binary, or label;
5. restrict the affected evidentiary role when a required semantic field is absent.

A schema difference that changes the scientific meaning of chronology, labels, clients, controls, cohorts, or operator validity is a scientific eligibility issue, not a parser convenience.

### Synthetic known-truth data

**Role:** known-truth mathematical/mechanism evidence.

The generator is specified in §21 and exposes the complete latent decomposition. Synthetic clients support theory, controlled complementarity, and sensitivity claims only.

### LAMDA

**Role:** primary real-data action-mechanism and prospective-security evidence when the acquired release satisfies the required chronology/operator conditions.

**Authoritative sources:** the LAMDA publication (arXiv:2505.18551) and the official Hugging Face repository `IQSeC-Lab/LAMDA`. The exact Hugging Face repository revision and every acquired file SHA-256 are recorded at acquisition.

The public released table is expected to contain the documented fields:

```text
hash
label
family
vt_count
year_month
feat_0 ... feat_4560
```

The official release documents 2013–2025 coverage with 2015 absent, more than one million samples, approximately 37% malware, 1,380 malware families, and a 4,561-feature variance-thresholded static basis. These values are sanity checks only; the acquisition manifest records the observed values.

Label handling is:

* use the released `label` field when present and internally consistent;
* independently audit it against `vt_count` using benign count `0`, malicious count at least `4`, and discard counts `1,2,3`;
* if the released label is absent but `vt_count` is present, derive the binary label by this fixed rule;
* if both are present and disagree, exclude the row and record the conflict.

Malware-family identity uses the released `family` field. Chronology uses `year_month` unless the acquired raw source provides a more precise timestamp whose semantics are verified and whose availability does not introduce future information. The roadmap does not assume a VirusTotal first-submission timestamp when the acquired release exposes only `year_month`.

The official public features have already undergone the documented variance-threshold selection. Therefore:

* when the acquired release is the documented 4,561-feature table, do **not** apply a second variance threshold;
* when an authorized raw pre-selection feature matrix is acquired instead, fit `VarianceThreshold(threshold=0.001)` using only the corresponding cutoff-safe training population and record the selected feature indices.

In either case, standardization is fitted only on the cutoff-safe training population and then applied unchanged to validation and later observations.

The public LAMDA schema does not establish a natural organization/source client identifier. The default real-data execution therefore treats LAMDA as one corpus-level client for action-mechanism evidence. Calendar quarters are temporal windows, not simultaneous clients. If an separately acquired authorized release contains a source/market/organization identifier, that field may define multiple clients only after the client-semantics audit verifies that it existed at cutoff and represents genuinely distinct sources; otherwise no LAMDA federation claim is made.

Problem-space APK operators require a raw APK whose cryptographic hash matches the released `hash`. The loader searches only the configured immutable raw-data root and any authorized AndroZoo-derived acquisition indexed by that hash. A sample lacking a matching APK remains usable for feature-space detection where otherwise eligible but is `operator_ineligible`.

### EMBER2024

**Role:** secondary chronological cross-corpus and source/format federation evidence.

**Authoritative sources:** the EMBER2024 publication (arXiv:2506.05074) and official repository `FutureComputing4AI/EMBER2024`. Acquisition records the exact repository commit/release identity and SHA-256 values of acquired files.

Official documentation describes collection from September 24, 2023 through December 14, 2024 at weekly resolution, with the first 52 weeks used as the original training period and the final 12 weeks as the original test period. It reports 30,000 Win32 PE files per week and 10,000 Win64 PE files per week, corresponding to 1,560,000/360,000 Win32 train/test files and 520,000/120,000 Win64 train/test files in that release. These are validation expectations; the acquired subset manifest is authoritative.

FedACT confirmatory execution uses Win32 PE and Win64 PE only. The chronology field is the acquired source collection/first-seen time documented by the pinned release. If only a week identity is available, use the beginning of that documented collection week as the conservative timestamp and preserve the original week identity.

Feature extraction uses the pinned EMBER2024/`thrember` feature-version-3 semantics implemented with `pefile`, including its documented PE feature groups. The implementation must not guess which columns are counts. It obtains feature-group metadata from the pinned extractor/schema and applies `log1p` only to fields explicitly declared as nonnegative count features; the exact transformed column identities are stored in the preprocessing manifest. Standardization is then fitted cutoff-safely.

Family, behavior, packer, and threat-group metadata may be used only when the acquired release actually contains them and the relevant annotation is available under §9. Missing family metadata does not block binary detector training but does block a family-defined confirmatory cohort.

Win32 versus Win64 is the fixed diagnostic source/format client substrate when both have sufficient simultaneous support. It is not represented as natural organization identity. Strong natural-organization claims remain prohibited.

Problem-space PE actions require raw PE bytes whose SHA-256/source identity matches the prepared sample. If the public feature release does not contain the original binary and no authorized matching binary exists under `data/raw`, that sample is `operator_ineligible`; features may not be inverted or approximated into a PE file.

Because the documented EMBER2024 time span is substantially shorter than LAMDA, §9.4 determines which configured horizons and cutoffs are actually observable. Missing long horizons are recorded as `MISSING_SOURCE_DATA`; the protocol is not shortened to force them.

## 10.2 Client semantics

Real client definitions are selected only from fields present in the acquired data, in this order:

1. natural organization identity;
2. natural sensor/source/collection identity with defensibly distinct nuisance processes;
3. diagnostic source/channel/platform identity;
4. one corpus-level client.

Random hashes, arbitrary shards, calendar periods, and retrospective clustering may not be reinterpreted as real clients.

Only categories 1–2 can support a strong natural-federation claim. Category 3 supports only source/platform complementarity, and category 4 supports local action-mechanism evidence but no federation claim.

The client-semantics audit records the source field, observed values, support, availability semantics, and permitted claim strength.

## 10.3 Cohort semantics

Confirmatory cohort construction is malware family crossed with corpus **only when the family label is present and cutoff-valid**.

Required fields:

```text
cohort_id
definition
availability_timestamp
dataset_id
client_id
support_count
window_start
window_end
eligibility_status
```

LAMDA uses `family`. EMBER2024 uses the pinned release's native family field only if observed and cutoff-valid. Missing/unknown family observations may remain in binary detector training but are excluded from family-cohort transition estimation and that exclusion is recorded.

`identification.minimum_support_per_class` applies independently to:

* malicious observations in each side of every transition;
* benign/control observations in each side of every control-transition replicate;
* each client/cohort/window unit used by identification.

No adjacent windows are pooled merely to pass support.

## 10.4 Control construction

Controls represent source/context nuisance rather than arbitrary benign resampling.

For LAMDA, a control observation must be benign under the fixed label rule and match the same available corpus/client context and calendar month as the malicious transition side. Historical control-transition replicates are distinct eligible transition endpoints/context cells inside the outer historical interval.

For EMBER2024, controls are benign files from the same Win32/Win64 format client and the same collection week where weekly support permits; otherwise the matching cell is the same calendar month. The chosen weekly-versus-monthly level is determined deterministically during preprocessing by whether every required side meets the support floor, preferring weekly matching. It is recorded once per cutoff and is not outcome-tuned.

A control-transition replicate always uses two adjacent matched temporal cells as defined in §8.2. Random splitting of one benign pool into pseudo-replicates is prohibited.

## 10.5 Data-quality and preprocessing rules

Preparation applies these deterministic rules before model fitting:

* duplicate sample identifiers/hashes with identical scientific fields: retain one canonical row, chosen by stable source-file/path order;
* duplicate identifiers with conflicting label, chronology, family, or feature content: exclude all conflicting rows and record `CONFLICTING_DUPLICATE`;
* malformed records or nonfinite feature values: exclude and record the reason;
* missing sample identity or chronology: exclude from chronological science;
* missing binary label: derive only from an explicitly permitted source field above; otherwise exclude;
* missing family: retain for binary detector training if otherwise eligible, but exclude from family-defined cohorts;
* no numerical feature is silently imputed;
* a feature with training standard deviation below `numerical.scale_standardization_floor` is removed by the fitted preprocessing transform and its identity is recorded.

Every exclusion count is reported by dataset, cutoff, and reason.

## 10.6 Real-data feasibility rule

A corpus may enter an evidence-producing workflow only for roles whose requirements pass:

```text
chronology valid
AND malicious history sufficient
AND controls sufficient for the requested identification role
AND required context fields observed
AND cohorts cutoff-safe where cohort analysis is requested
AND raw operator artifacts available for operator-dependent evidence
AND representation trainable without leakage
```

Failure narrows the evidentiary role rather than causing the implementation to invent missing source semantics. For example, absence of a natural client identity removes natural-federation claims; absence of raw binaries removes operator-dependent units; absent family labels remove family-cohort units.

# 11. Representation and Detector Specification

## 11.1 Cutoff-fixed scientific semantics

For each representation retraining cutoff,

\[
E_T:x\rightarrow z\in\mathbb R^{64}
\]

is trained only from permitted historical information and then remains immutable throughout all scientific producers that reference its checkpoint identity.

The detector is

\[
f_\phi(x)=\sigma(h_\phi(E_T(x))).
\]

Hardening changes only the detector head; it never changes the encoder used to define transition/action geometry for that cutoff.

## 11.2 Architecture

The representation network is:

```text
input
→ Linear(input_dimension, 512)
→ BatchNorm1d(512)
→ ReLU
→ Dropout(0.10)
→ Linear(512, 256)
→ BatchNorm1d(256)
→ ReLU
→ Dropout(0.10)
→ Linear(256, 64)
```

The 64-dimensional output layer is linear.

The detector head is:

```text
Linear(64, 1)
```

Training operates on logits. Sigmoid is applied only for probability-valued inference.

## 11.3 Base training objective and randomness

At each full-retraining cutoff, train the encoder and detector head jointly on the cutoff-safe binary malware task using mean, unweighted `BCEWithLogitsLoss`.

Randomness is separated as follows:

* the corresponding `seeds.representation` value initializes encoder parameters;
* the paired `seeds.detector_training` value initializes detector-head parameters and the training mini-batch/data-loader random stream.

Seed index \(i\) in the two arrays forms one paired training replicate; seed streams are never substituted for one another.

Training uses Adam with zero weight decay and a cosine annealing schedule from `training.initial_learning_rate` to `training.final_learning_rate` across `training.maximum_epochs`. Batch size and early-stopping patience come from configuration.

## 11.4 Validation and checkpoint selection

The validation fraction is configured. Splitting is stratified jointly by binary label and calendar month whenever a stratum contains at least two observations. A singleton stratum remains in training and is recorded as `VALIDATION_STRATUM_TOO_SMALL`; it is never duplicated across train and validation.

Within a retraining cutoff, choose the epoch with the lowest mean validation `BCEWithLogitsLoss`. Exact ties within `numerical.projection_tie_tolerance` go to the earlier epoch. Early stopping counts epochs without a validation-loss improvement greater than that tolerance.

The encoder and detector-head checkpoints exported for downstream use come from the same selected epoch.

## 11.5 Prediction rule

For FNR, TPR, FPR, confusion matrices, clean-cost gates, and other categorical detector endpoints:

\[
\hat y=\mathbf1[\sigma(h_\phi(E_T(x)))\ge0.5].
\]

The 0.5 operating threshold is fixed and is not tuned by prospective outcomes. PR-AUC and ROC-AUC use the continuous sigmoid score.

## 11.6 Preprocessing

Dataset-specific input preprocessing is governed exclusively by §10 and is fitted only on the corresponding cutoff-safe training population. The observed post-preprocessing feature dimension becomes `input_dimension`; no roadmap count overrides the acquired schema.

## 11.7 Retraining/reuse

The encoder/head pair is retrained at `temporal.full_retraining_interval_months`. Intermediate monthly cutoffs reuse the most recent compatible pair whose training information boundary precedes the cutoff. Reuse is governed by artifact fingerprints, not by an informal cache.

## 11.8 Checkpoint provenance

Each representation checkpoint records:

```text
dataset
training_cutoff
architecture
input_dimension
embedding_dimension
preprocessing_manifest_hash
training_manifest_hash
representation_seed
detector_seed
selected_epoch
validation_loss
checkpoint_hash
dependency_fingerprint
producer_code_fingerprint
repository_commit
```

The detector checkpoint references the exact representation checkpoint hash and selected epoch.

# 12. Domain-Valid Action / Operator Specification

## 12.1 Operator record and deterministic enumeration

Every operator instance is represented by:

```text
operator_name
dataset
domain
semantic_validity_contract
construction_function
parameter_domain
eligibility_rule
rejection_rule
representation_displacement_rule
zero_displacement_rule
maximum_uses_per_sample
provenance
```

Candidate enumeration is deterministic:

1. enumerate applicable atomic families in the order listed below;
2. enumerate each family's parameter grid in ascending/lexicographic canonical order;
3. generate compositions of length 1 through `operators.maximum_composed_atomic_actions`;
4. never repeat the same atomic family in one composition;
5. reject a composition whose later atomic action invalidates the precondition of an earlier action;
6. canonicalize a composition by listed-family order, so permutations of the same compatible actions are not duplicate candidates.

All stochastic payload choices use the paired `seeds.operator` stream and are recorded.

A problem-space operator is constructed only from the verified original raw artifact. A feature vector may never be edited as a substitute for an executable PE/APK transformation.

## 12.2 Statistical displacement

For eligible \((x,o)\),

\[
d_o(x)=E_T(o(x))-E_T(x).
\]

Reject the action when

\[
\|d_o(x)\|_2<\texttt{numerical.zero＿displacement＿floor}.
\]

Otherwise

\[
q_o(x)=\frac{d_o(x)}{\|d_o(x)\|_2}.
\]

## 12.3 EMBER2024 PE operator contract

PE manipulation uses the project-pinned LIEF, `pefile`, and, for the pack/unpack family, UPX executable identities recorded in the environment manifest.

Allowed atomic families and exact parameter domains are:

| Operator | Parameter domain | Eligibility / construction | Mandatory rejection |
| --- | --- | --- | --- |
| Append benign EOF bytes | payload sizes 64, 256, 1024 bytes | append deterministic bytes sampled from cutoff-safe benign byte fragments | transformed file fails PE parsing/execution/behavior/maliciousness validation |
| Fill existing section slack | payload sizes 64, 256, 1024 bytes, truncated to available slack | write only into verified file-backed slack not referenced by a data directory | insufficient slack or any validator failure |
| Add unused import | one of `GetVersion`, `GetTickCount`, `GetLastError`, `CloseHandle` from a compatible standard Windows library | add import entry without inserting a call site | import-table rebuild fails or any validator failure |
| Rename section | canonical safe names `.data1`, `.rdata1`, `.text1` not already present | rename one non-special section without changing raw content/permissions | name collision, loader/parser failure, or any validator failure |
| Add read-only section | payload sizes 256 or 1024 bytes | add non-executable read-only section containing cutoff-safe benign bytes | section-layout failure or any validator failure |
| Entry-point trampoline | no numerical parameter | insert architecture-correct unconditional jump stub that transfers immediately to original entry point | unsupported machine architecture, relocation/layout failure, or any validator failure |
| Remove Authenticode directory | none | clear certificate-table directory and remove certificate blob where safely supported | structural failure or any validator failure |
| Zero PE checksum | none | set optional-header checksum to zero | missing compatible optional header or any validator failure |
| Remove debug directory | none | remove/clear debug-directory records without touching executed code | malformed directory or any validator failure |
| UPX pack/unpack | action in `{pack, unpack}` | use the recorded UPX executable; require `upx -t` success after transformation | UPX unsupported/refused or any validator failure |

A family is applied at most once per source sample/composition.

## 12.4 LAMDA APK operator contract

APK manipulation uses a project-pinned Android build toolchain, APK parser, and Android emulator image recorded in provenance.

Allowed atomic families are:

| Operator | Parameter domain | Eligibility / construction | Mandatory rejection |
| --- | --- | --- | --- |
| Unreachable benign gadget injection | one gadget from the cutoff-safe project benign-gadget library | add a non-exported helper class/method that is unreachable from existing application call paths and requests no new permissions | manifest/code rebuild/sign/install failure, new permission/exported component, reachable side effect, or any validator failure |
| Permission-neutral resource injection | payload size 256, 1024, or 4096 bytes | add an unreferenced packaged resource containing deterministic cutoff-safe benign bytes | manifest permission change, resource collision/reference, rebuild/sign/install failure, or any validator failure |

The benign-gadget/resource source library contains only assets whose source timestamp and acquisition identity precede the evaluated cutoff. Its hashes are part of the operator-library identity.

## 12.5 Structural, execution, maliciousness, and behavior validation

Every generated candidate passes all four validation layers before statistical evaluation.

### Structural validity

* PE: both `pefile` and LIEF must parse the transformed binary and report the expected machine type.
* APK: the project APK parser/build tool must parse the package, manifest, resources, and DEX files; package identity must be preserved except for a deterministic temporary signing identity required solely for emulator installation.

### Execution smoke validity

PE source and transformed samples are executed in the same isolated Windows sandbox image with no external network access for `operators.validation.execution_timeout_seconds`. The sandbox image hash, OS build, launcher, and observation harness are recorded.

APK source and transformed samples are installed and launched in the same project-pinned Android emulator image through ADB. Each receives `operators.validation.android_monkey_events` deterministic UI events generated from the applicable operator seed. A transformed sample fails if it introduces a launch/install failure, crash, or ANR not observed for the source under the same harness.

### Maliciousness preservation

The study uses ClamAV 1.5.4 with one study-wide signature-database snapshot whose file hashes and publication timestamp are recorded before prospective evaluation. The source artifact must be detected as malicious by that engine, and the transformed artifact must remain detected. A source that is not detected is `MALICIOUSNESS_VALIDATION_UNAVAILABLE` and is not confirmatory operator evidence.

This independent check supplements, but does not replace, the corpus label.

### Dynamic-smoke behavior preservation

The sandbox/emulator emits a canonical set of observable events: launched processes/components, created files, modified files, registry or preference writes where available, network-attempt destinations, and loaded modules/libraries. Remove harness-only events and compute Jaccard similarity between source and transformed event sets.

A candidate is behavior-preserving when

\[
J(A,B)=\frac{|A\cap B|}{|A\cup B|}
\ge
\texttt{operators.validation.minimum＿behavior＿jaccard}.
\]

If both event sets are empty, the check is uninformative and the candidate is not valid for confirmatory operator evidence.

## 12.6 Coverage and validity order

Domain validation occurs before action-interval evaluation. Thus

\[
\text{statistical support}+\text{domain invalid}
\Rightarrow \text{REJECT}.
\]

For a cohort/window, valid-operator coverage is

\[
\frac{
\#\lbrace\text{operator-eligible source samples with at least one valid nondegenerate candidate}\rbrace
}{
\#\lbrace\text{operator-eligible source samples}\rbrace
}.
\]

If the denominator is zero or coverage is below `operators.minimum_valid_coverage`, operator-dependent execution emits `ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT`.

## 12.7 Provenance

Every candidate records:

```text
operator_name
source_sample_id
representation_hash
cutoff
cohort
horizon
operator_parameters
source_hash
output_hash
toolchain_identity
validity_status
validity_evidence
q_hash
```

The operator-family definitions and validation semantics are part of the producer-code/dependency fingerprint. They may not be changed after inspecting the corresponding later-real outcomes.

# 13. Federated System and Information-Exchange Specification

## 13.1 Client role

Each client:

* computes malicious transitions;
* constructs matched controls;
* estimates nuisance bases;
* estimates uncertainty components;
* evaluates local control quality;
* transmits low-rank summaries.

Raw samples are not required by the transition-identification protocol itself. Raw artifacts remain necessary locally for domain-valid operator construction where that client participates in operator-dependent evaluation.

## 13.2 Server role

The server:

* validates client summaries;
* intersects compatible constraints;
* propagates feasible sets;
* solves action support problems;
* generates action certificates;
* coordinates hardening;
* records abstention.

## 13.3 Communication payload

Per eligible client/cohort/window:

\[
(
\hat U_k,
y_k,
\hat\Sigma_k,
n_k^{M,-},
n_k^{M,+},
n_k^B,
\hat\gamma_k,
\hat\beta_k,
d_k^{control}
).
\]

The server computes

\[
\hat P_kv =
v-\hat U_k(\hat U_k^\top v)
\]

without receiving a dense \(d\times d\) projector.

Every payload field has one canonical serialization for communication-cost accounting under §16.

## 13.4 Separation of federated roles

Three distinct concepts must never be conflated.

### Identification federation

Client summaries jointly construct the FedACT feasible transition set.

### Detector-training federation

Ordinary federated training of the detector, where used as a comparator.

This is not the FedACT novelty mechanism.

### Client-selection federation

Optional communication-limited client selection.

This is secondary experimental-design machinery.

## 13.5 Participation

Core identification uses every client passing the predeclared quality criteria unless the experiment explicitly manipulates client subsets. A federation claim requires at least two quality-eligible clients. A one-client feasible set remains valid local action-mechanism evidence but may not be described as federated identification.

## 13.6 Trust

Primary claim:

* authenticated, honest organizations/sources;
* non-IID data;
* imperfect controls;
* private/local transitions.

Stress tests may inject corrupted summaries.

No Byzantine-security guarantee is permitted.

# 14. Baseline and Comparator Strategy

Every comparator below has an executable identity. A comparator that depends on an external published implementation is acquired from the named official author repository when available; the exact commit/release and dependency environment are recorded before that comparator is used. If the publication and public implementation together do not specify enough information to reproduce the method without inventing scientific hyperparameters, that comparator is `NOT_APPLICABLE` under the explicit eligibility rule below rather than being approximated ad hoc.

## 14.1 Identification baselines

All point estimators use the same cutoff-safe transition/control summaries as FedACT unless the baseline definition intentionally removes controls.

Let the stacked whitened projected system be

\[
A=
\begin{bmatrix}
\hat\Sigma_1^{-1/2}\hat P_1\\
\vdots\\
\hat\Sigma_K^{-1/2}\hat P_K
\end{bmatrix},
\qquad
b=
\begin{bmatrix}
\hat\Sigma_1^{-1/2}\hat P_1y_1\\
\vdots\\
\hat\Sigma_K^{-1/2}\hat P_Ky_K
\end{bmatrix},
\qquad
H=A^\top A.
\]

| Comparator | Executable definition | Scientific purpose |
| --- | --- | --- |
| Raw malicious-transition forecast | effective-support-weighted mean of \(y_k\), followed by the same scalar temporal model as FedACT | tests value of controls |
| Matched benign subtraction | subtract each client's weighted mean control transition \(\bar b_k\) from \(y_k\), then combine client vectors by geometric median | tests whether multidimensional nuisance geometry is necessary |
| Projected-inverse point reconstruction | \(A^\dagger b\) | point-identification comparator |
| Best individual client | minimum-norm solution from the client having smallest \(\beta_k\); ties by larger malicious effective support then lexical client id | tests federation |
| Single pooled nuisance subspace | estimate one nuisance basis from all eligible control-transition replicates pooled with effective-support weights, then solve the corresponding point system | tests heterogeneous control geometry |
| Average projected residual | effective-support-weighted mean of \(\hat P_ky_k\) | simple projected comparator |
| Standard pseudoinverse | \(A^\dagger b\) with numerical pseudoinverse cutoff `numerical.rank_clip_epsilon_relative` | point reconstruction |
| Regularized point reconstruction | \((H+\lambda I)^{-1}A^\top b\), with \(\lambda=\max(\epsilon_{\rm scale},c_{\rm ridge}\mathrm{tr}(H)/d)\) | regularization alternative |
| Covariance-weighted projected point | weighted least-squares solution of the stacked system above | statistically stronger point comparator |
| Robust raw aggregation | geometric median of \(y_k\) | nuisance-agnostic robust aggregation |
| Nuisance projection without global intersection | geometric median of \(\hat P_ky_k\) | tests intersection geometry |
| Same feasible set, generic robust training, no certificate | rank valid actions by alignment to the propagated Chebyshev center and use the same action count/hardening budget without the interval certificate | isolates certificate value |
| Point estimate plus matched isotropic uncertainty | center the propagated point estimate in an L2 ball whose radius is selected by the same nested inner-cutoff procedure to match FedACT's certification rate as closely as possible | tests direction-specific sharp bounds |

The geometric median is computed by Weiszfeld iteration with `numerical.solver.absolute_tolerance` convergence tolerance and `numerical.solver.maximum_iterations`; an iterate landing on an observation returns that observation according to the standard modified-Weiszfeld rule. The ridge coefficient \(c_{\rm ridge}\) is `baselines.point_ridge_relative`.

## 14.2 Temporal and security baselines

### Chronological static ERM

Uses the exact representation/detector architecture, optimizer, loss, validation split, retraining cadence, and categorical decision threshold from §11, without FedACT hardening.

### Temporal invariance

Use TIF, *Learning Temporal Invariance in Android Malware Detectors* (Zheng, Yang, Ngai, Jana, and Cavallaro; arXiv:2502.05098), from the authors' official implementation. For the tabular-input adaptation, retain the FedACT input feature basis and 64-dimensional representation capacity, and use the publication/repository training settings:

```text
stage 1: batch=512, learning_rate=1e-4, contrastive_weight=1.0,
         weight_decay=0, epochs=30, proxy_count=3
stage 2: batch=1024, learning_rate=1e-4, contrastive_weight=0.1,
         weight_decay=1e-3, epochs=20, proxy_count=3, patience=5
invariance_penalty=1.0
```

No later-real outcome is used to alter those settings. If the acquired official implementation exposes a mandatory parameter not determined by these settings or by the dataset input dimension, use its repository default and record it in the baseline manifest.

### Future-malware-prediction comparator

The named comparator *Counteracting Concept Drift by Learning with Future Malware Predictions* (arXiv:2404.09352) is used only if, at implementation time, an author-maintained public implementation exists or the publication plus supplementary material specifies every required architecture/training parameter for the applicable static-feature modality. Otherwise it is `NOT_APPLICABLE`. FedACT does not invent a GAN architecture to force this comparator into the study.

The independently required **raw future-transition forecast without controls** remains executable through the scalar temporal point forecast defined in §14.1 and does not depend on this external comparator.

### Reactive drift adaptation

Use Transcendent (Jordaney et al., USENIX Security 2017) from the authors' public `s2labres/transcendent-release` implementation. Its credibility/rejection thresholds are selected only by the same nested pre-cutoff discipline. Retraining receives labels only when those labels become available under the baseline's operational chronology.

### Static valid-mutation adversarial training

At each malicious training sample, rank all domain-valid nondegenerate mutations by current detector loss and train on the worst valid actions up to the same per-sample action count used by FedACT. Use the same detector-only hardening optimizer/budget as §8.3. It receives no transition-set information.

### Random valid mutation

Sample without replacement from the same valid candidate pool, using `seeds.baseline`, with the same action count and hardening budget as FedACT.

### Static generative augmentation

Use a VAE on the cutoff-safe malicious 64-dimensional representations:

```text
encoder: 64 → 256 → 128 → (mu:64, logvar:64)
decoder: 64 → 128 → 256 → 64
hidden activation: ReLU
reconstruction loss: mean squared error
KL weight: 1.0
optimizer: Adam
learning-rate schedule / epochs / patience: same as §11
```

The number of generated malicious representations equals the number of FedACT challenge representations in the matched comparison. Generated representations are detector-training inputs only and are not treated as domain-valid executable malware.

### Temporal domain-generalization and label-efficient adaptive methods

Include the closest public method only when an author/public implementation supports the available static-feature modality without adding unavailable information or when the publication fully specifies all required architecture and optimization parameters. Otherwise record `NOT_APPLICABLE` with the eligibility reason. This rule is evaluated before prospective outcomes.

## 14.3 Federation baselines

### Centralized equivalent

Pool the same cutoff-safe observations/controls available to participating clients and execute the corresponding centralized control/set construction. It is a reference, not a privacy claim.

### Local-only equivalent

Construct the same FedACT client constraint and action intervals one client at a time.

### Ordinary federated detector

Train the §11 detector architecture with synchronous full participation over quality-eligible real clients. Each communication round performs one local epoch with Adam using the §11 learning-rate schedule indexed by round. Aggregate encoder/head parameters by standard sample-count-weighted FedAvg. Use `training.maximum_epochs` as the maximum round count and the same validation-loss early-stopping patience as §11. The client-specific training samples remain local; no FedACT identification summaries enter this baseline.

### Redundant/complementary and randomized-geometry conditions

Use exactly the manipulations in §§22 and 29 with matched total samples. No additional model is introduced.

## 14.4 Baseline fairness contract

Where applicable, match:

* representation capacity and binary detector head;
* cutoff and historical information;
* validation information and tuning budget;
* operator validity and candidate source population;
* number of hardening challenges;
* optimization budget;
* evaluation horizon and later-real population;
* adaptation information budget.

A comparator may not receive future information unavailable to FedACT at the corresponding operational time, and FedACT may not receive an information advantage unrelated to the scientific mechanism.

Baseline acquisition identity, applicability decision, all effective hyperparameters, and parity results are recorded before the baseline enters confirmatory evaluation.

# 15. Ablation Strategy

| Ablation                                                             | Component tested                 | Alternative explanation                            | Expected consequence                             |
| -------------------------------------------------------------------- | -------------------------------- | -------------------------------------------------- | ------------------------------------------------ |
| No controls: set nuisance projector to identity                      | control evidence                 | raw temporal change is sufficient                  | more nuisance contamination                      |
| Single matched control displacement rather than nuisance span        | multidimensional controls        | subtraction is enough                              | degradation under amplitude mismatch             |
| Replace feasible set by point reconstruction                         | set-valued estimand              | point estimate sufficient                          | more false action confidence                     |
| Replace action-specific interval with global spectral gate           | decision-specific identification | global observability sufficient                    | mismatch at fixed global rank                    |
| Matched-radius isotropic uncertainty set                             | control-derived geometry         | generic conservatism explains gain                 | weaker certificate relevance                     |
| Set subspace-estimation contribution to zero                         | finite-sample calibration        | subspace error irrelevant                          | false certification at low control support       |
| Set \(\rho\) to `ablations.zero_control_span_violation_budget`      | residual nuisance robustness     | controls exactly span nuisance                     | undercoverage under violation                    |
| Set \(\xi\) to `ablations.zero_private_contamination_budget`        | private-transition allowance     | global transition fully shared                     | inconsistency/false confidence under local modes |
| Shuffle historical order                                             | temporal information             | static geometry sufficient                         | reduced prospective value                        |
| Identity/no-change dynamics                                          | forecast contribution            | current identified set sufficient                  | horizon-specific degradation                     |
| Randomize support/action association while preserving validity/count | semantic action mapping          | any valid augmentation works                       | later relevance collapses                        |
| Retain only the lower-bound threshold and remove the width gate      | ambiguity-width rule             | lower bound alone sufficient                       | greater radius sensitivity                       |
| Use true nuisance spaces                                             | nuisance estimation error        | synthetic upper bound                              | isolates estimation loss                         |
| Use true transition                                                  | identification/forecast loss     | synthetic upper bound                              | isolates downstream hardening loss               |
| Remove cross-client intersection                                     | federation                       | local controls sufficient                          | larger intervals when controls complement        |
| Produce certificates but do not harden                               | defensive consequence            | identification useful but downstream effect absent | no detector change                               |

Each ablation uses the same configuration contract rather than redefining scientific parameters.

---

# 16. Metric and Evaluation Semantics

## 16.1 Identification and calibration metrics

### Set coverage

For known-truth synthetic data,

\[
\mathrm{Coverage}_{set} =
\frac1N\sum_{i=1}^N
\mathbf1[g_i^{true}\in\mathcal G_i].
\]

### Action-interval coverage

\[
\mathrm{Coverage}_{action} =
\frac1N\sum_i
\mathbf1[q_i^\top g_i^{true}\in[L_i,U_i]].
\]

### Action width

\[
W_o=U_o-L_o.
\]

### Certification rate

\[
\mathrm{CertRate} =
\frac{\#\lbrace\text{valid candidate actions certified}\rbrace}
{\#\lbrace\text{valid candidate actions evaluated}\rbrace}.
\]

### Ambiguity rate

\[
\mathrm{AmbRate} =
\frac{\#\lbrace L_o<\tau_{align}\le U_o\rbrace}
{\#\lbrace\text{valid candidate actions evaluated}\rbrace}.
\]

### Abstention rate

\[
\mathrm{AbstentionRate} =
\frac{\#\lbrace\text{eligible cohort/horizon units with no actionable certificate}\rbrace}
{\#\lbrace\text{eligible cohort/horizon units}\rbrace}.
\]

### False-certification rate

For known-truth simulation,

\[
R_o^{true}=\mathbf1[q_o^\top g^{true}\ge\tau_{align}],
\]

\[
\mathrm{FCR} =
\frac{
\sum_o\mathbf1[\mathrm{Cert}_o=1\land R_o^{true}=0]
}{
\sum_o\mathbf1[\mathrm{Cert}_o=1]
}.
\]

If no action is certified, report `UNDEFINED_NO_CERTIFICATES`.

## 16.2 Later-real action relevance

For real data, §Configuration-linked definitions constructs \(\hat g^{real}_{c,(T,T+h]}\). Define

\[
A_o^{real}=q_o^\top\hat g^{real}_{c,(T,T+h]}.
\]

The executable later-real relevance indicator is

\[
R_o^{real} =
\mathbf1[
A_o^{real}\ge\tau_{align}
].
\]

The threshold is the same pre-cutoff \(\tau_{align}\) used by the corresponding certificate; no later-real relevance threshold is tuned separately.

### Certificate precision

\[
\mathrm{Precision}_{cert} =
\frac{TP_{cert}}{TP_{cert}+FP_{cert}},
\]

where TP/FP compare certificate state with \(R_o^{real}\). A zero denominator is `UNDEFINED_NO_CERTIFICATES`.

### Certificate recall

\[
\mathrm{Recall}_{cert} =
\frac{TP_{cert}}{TP_{cert}+FN_{cert}}.
\]

A zero denominator is `UNDEFINED_NO_RELEVANT_ACTIONS`.

### Cosine future alignment

When \(\|\hat g^{real}\|_2>0\),

\[
\mathrm{CosAlign} =
\frac{q_o^\top\hat g^{real}}{\|\hat g^{real}\|_2}.
\]

Otherwise it is undefined.

### Rank alignment

Rank alignment is Spearman's \(\rho\) between predicted lower bound \(L_o\) and later-real alignment \(A_o^{real}\), computed within cutoff over valid actions. It is diagnostic and is not a separately tunable statistical procedure.

## 16.3 Geometry diagnostics

### Prospective-set diameter bound

The executable set-size quantity is the coordinate-support upper bound from §8.3:

\[
D_{\mathrm{box}}(\mathcal G) =
\sqrt{\sum_{j=1}^{d}(u_j-l_j)^2}.
\]

The exact Euclidean diameter may additionally be reported in analytical cases where available, but no alternative proxy may drive the abstention gate.

### Action-conditioning index

\[
\kappa_{act}(q;H)=\sqrt{q^\top H^\dagger q}.
\]

### Smallest positive frame eigenvalue

\[
\lambda_{\min}^+(H) =
\min\lbrace\lambda_i(H):\lambda_i(H)>
\texttt{numerical.rank＿clip＿epsilon＿relative}\lambda_{\max}(H)\rbrace.
\]

If no eigenvalue exceeds the threshold, report `UNDEFINED_NO_POSITIVE_SPECTRUM`.

### Client action gain

\[
\Delta_j(q\mid\mathcal K) =
W_q(\mathcal G_{\mathcal K}) -
W_q(\mathcal G_{\mathcal K\cup\lbrace j\rbrace}).
\]

### Weighted client gain

\[
\Delta_j^{act} =
\sum_{q\in\mathcal Q}\pi_q\Delta_j(q\mid\mathcal K).
\]

The weights are fixed by §32.

## 16.4 Detector and security metrics

### False-negative, true-positive, and false-positive rates

\[
\mathrm{FNR}=\frac{FN}{FN+TP},
\qquad
\mathrm{TPR}=1-\mathrm{FNR},
\qquad
\mathrm{FPR}=\frac{FP}{FP+TN}.
\]

A zero denominator produces `UNDEFINED` and the denominator count is reported.

### PR-AUC and ROC-AUC

Compute on the continuous sigmoid score over the complete declared evaluation population. A metric requiring both classes is `UNDEFINED` when that class support is absent.

### Early-horizon FNR

For endpoint \(H_e=\texttt{temporal.early＿horizon＿months}\),

\[
\mathrm{EarlyFNR} =
\frac{
\sum_{t\le H_e}FN_t
}{
\sum_{t\le H_e}(FN_t+TP_t)
}.
\]

### Pre-adaptation exposure

Partition \([T,T_{\mathrm{adapt}})\) into calendar-month evaluation bins. For bin \(m\), let \(\Delta_m\) be its number of covered days. Define duration weights

\[
w_m=\frac{\Delta_m}{\sum_j\Delta_j}.
\]

Then

\[
\mathrm{Exposure} =
\sum_m w_m\mathrm{FNR}_m.
\]

The endpoint includes only bins before the reactive comparator is permitted to incorporate the corresponding feedback.

### Time to catch-up

Time to catch-up is the first permitted chronological monthly evaluation boundary at which a reactive comparator simultaneously satisfies

\[
\mathrm{FNR}_{reactive}\le\mathrm{FNR}_{FedACT}
\]

and

\[
\mathrm{FPR}_{reactive}\le\mathrm{FPR}_{FedACT}
\]

on the same accumulated later-real population. If this never occurs in the observable horizon, report right-censored at the last observable boundary.

### Clean-data degradation

The primary clean-cost gate is absolute validation FNR degradation in percentage points:

\[
\Delta\mathrm{FNR}_{clean,pp} =
100(
\mathrm{FNR}_{hardened} -
\mathrm{FNR}_{base}
).
\]

Other clean metrics may be reported secondarily.

### Hardening benefit

For a loss-like endpoint \(E\),

\[
\Delta E=E_{baseline}-E_{FedACT}.
\]

Positive values favor FedACT.

## 16.5 Communication cost

Canonical payload serialization for communication accounting is:

* floating arrays \(\hat U_k,y_k,\hat\Sigma_k\): contiguous little-endian IEEE-754 float32;
* integer counts: little-endian signed int64;
* scalar diagnostics/radii: little-endian IEEE-754 float64;
* strings/enums: UTF-8 bytes preceded by a little-endian uint32 byte length.

Protocol framing, transport encryption, and network headers are excluded and reported separately if measured.

Per client,

\[
C_k=\mathrm{bytes}(\text{canonical payload}),
\qquad
C_{total}=\sum_{k\in\mathcal K_{selected}}C_k.
\]

# 17. Statistical Analysis Protocol

## 17.1 Unit of inference

Rolling external cutoffs are the primary repeated units.

Hierarchy:

```text
dataset
  → cutoff
    → cohort
      → client/action/horizon
        → seed
```

Actions, cohorts, and clients within one cutoff are not treated as independent top-level replicates.

## 17.2 Confirmatory endpoints

Primary endpoint families:

1. action-certification precision / prospective relevance;
2. early-horizon FNR or, where prespecified for the comparator, pre-adaptation exposure.

Secondary endpoints:

* action width;
* certification/ambiguity/abstention rates;
* PR-AUC and ROC-AUC;
* clean cost;
* time-to-catch-up.

## 17.3 Within-cutoff aggregation

Before any cutoff-level paired test or interval, construct one value per method/contrast/cutoff/seed:

* certificate precision: pool TP and FP across all eligible confirmatory cohort/action units at the primary horizon, then compute one precision;
* early-horizon FNR: pool FN and TP across the declared early-horizon evaluation population;
* exposure: use §16's duration-weighted exposure;
* action width: median over eligible action units;
* federation width contrast: median paired action-width difference over action units present in both compared conditions;
* future-alignment group contrast: difference in median \(A_o^{real}\) between the two matched action groups.

For a cutoff with multiple planned random seeds, compute the arithmetic mean of its finite seed-level endpoint values after applying §17.8 missingness rules. This single cutoff value enters confirmatory inference. A seed is never replaced by another seed.

## 17.4 Pairing

Comparisons are paired whenever methods share dataset, cutoff, cohort population, action/test population, and planned seed index. Randomized ablations use the same compatible upstream artifacts.

A cutoff enters a paired contrast only when both compared methods have a defined endpoint or when a prespecified scientific abstention/infeasibility rule explicitly defines the endpoint treatment below.

## 17.5 Confidence intervals and paired tests

Confidence intervals use a cutoff-clustered BCa bootstrap with `statistics.bootstrap.resamples` resamples and the `seeds.analysis` stream. A bootstrap draw samples cutoffs with replacement and carries the complete cutoff aggregate with it.

Confirmatory paired comparisons use a two-sided Wilcoxon signed-rank test on paired cutoff aggregates. Use Pratt handling for exact-zero differences. When the number of nonzero paired differences is at most `statistics.wilcoxon.maximum_nonzero_pairs_for_exact`, there are no ties in absolute nonzero differences, and the software implementation supports the exact distribution, use the exact p-value. Otherwise use the asymptotic normal approximation with continuity correction.

Matched-pairs rank-biserial correlation is the paired effect-size measure.

At least `statistics.minimum_paired_cutoffs` paired cutoff aggregates are required for confirmatory inference; otherwise the contrast is `INSUFFICIENT_EVIDENCE`.

Quantiles use linear interpolation, equivalent to NumPy `method="linear"` / R type 7.

## 17.6 Multiplicity

Benjamini-Hochberg control at `statistics.multiplicity.q` is applied separately to each prespecified confirmatory family:

1. certification-mechanism family within each dataset at the primary horizon: certified vs point-positive ambiguous and certified vs matched random valid;
2. security-outcome family within each dataset: FedACT vs each principal baseline for the prespecified primary FNR/exposure endpoint;
3. federation family within each dataset or synthetic confirmatory system: complementary vs redundant and federated vs local where both are confirmatory.

Cross-corpus tests constitute the corresponding second-dataset family and are not pooled into the primary-dataset BH denominator. Sensitivity and diagnostic tests are labeled as such and do not enter these confirmatory BH families.

If a family contains one test, report its unadjusted p-value without applying a one-element correction.

## 17.7 Seeds

Separate conceptual randomness uses the descriptive streams under `seeds`. Seed arrays are paired by index when a workflow needs more than one stream. No prose-defined seed silently overrides configuration.

## 17.8 Missing data and failed runs

Classify every unavailable result as:

```text
INFRASTRUCTURE_FAILURE
NUMERICAL_FAILURE
SCIENTIFIC_INFEASIBILITY
ASSUMPTION_VIOLATION
EXPECTED_ABSTENTION
MISSING_SOURCE_DATA
```

Treatment is fixed:

* infrastructure failures are retried under identical scientific inputs and do not become observations;
* an action-level expected abstention remains in certification/abstention denominators but produces no certificate TP/FP;
* scientific infeasibility remains in infeasibility/abstention accounting and is never silently dropped from workflow summaries;
* numerical failure, assumption violation, and missing source data remain explicitly missing for the affected endpoint and cannot be converted to a favorable value;
* a cutoff with undefined certificate precision because it has no certificates is not assigned precision zero; it remains `UNDEFINED_NO_CERTIFICATES` and contributes to abstention/certification metrics;
* a confirmatory contrast is `INSUFFICIENT_EVIDENCE` when more than `statistics.maximum_missing_cutoff_fraction` of otherwise time-eligible paired cutoffs are unavailable for numerical/assumption/source reasons, or when fewer than the minimum paired cutoffs remain.

All planned cutoff and seed counts, exclusions, and reasons are reported.

## 17.9 Outliers

No outcome-based exclusion is permitted. Data-quality exclusions arise only from §10 or other upstream eligibility contracts.

## 17.10 Decision criteria

A directional confirmatory hypothesis is **SUPPORTED** only when all applicable conditions hold:

1. the observed cutoff-level effect has the prespecified favorable direction;
2. the `statistics.confidence_level` BCa interval for the paired effect excludes zero in the favorable direction;
3. the applicable BH-adjusted p-value is below `statistics.multiplicity.q`, or the single-test unadjusted p-value is below \(0.05\);
4. any endpoint-specific material-effect gate is met;
5. §17.8 missingness requirements are met.

It is **FALSIFIED** when the BCa interval excludes zero in the prespecified contradictory direction, or when a hypothesis states an explicit failure condition that is met. It is **INSUFFICIENT_EVIDENCE** otherwise.

For the primary material-effect gates:

* early-horizon FNR must improve by at least `statistics.minimum_material_effects.early_horizon_fnr_absolute_reduction_percentage_points` absolute percentage points;
* action-certification precision must improve by at least `statistics.minimum_material_effects.action_certification_precision_absolute_increase` at the matched certification rate defined in §26;
* known-truth set/action coverage is materially below nominal when its deficit exceeds `statistics.minimum_material_effects.maximum_coverage_deficit_absolute` and the binomial Wilson confidence interval excludes the nominal target in the adverse direction.

For hypotheses without a separate numerical materiality threshold, the favorable direction plus the confidence/p-value criteria above is the prespecified evidentiary gate; no new post-outcome effect threshold is invented.

# Configuration YAML

This section reproduces the single authoritative production configuration file `configs/fedact.yaml`. It contains only primitive numerical parameters, candidate grids, seeds, categorical experiment values, and filesystem identifiers. Dataset-observed facts and runtime-measured values are recorded in manifests rather than configuration.

```yaml
datasets:
  lamda:
    labels:
      benign_detection_count: 0
      malware_minimum_detection_count: 4
      discard_detection_counts: [1, 2, 3]
    preprocessing:
      raw_variance_threshold_when_required: 0.001
  ember2024:
    confirmatory_formats: [win32_pe, win64_pe]

temporal:
  historical_training_window_months: 12
  transition_interval_months: 3
  cutoff_step_months: 1
  full_retraining_interval_months: 3
  forecast_horizons_months: [1, 3, 6, 12]
  primary_confirmatory_horizon_months: 3
  early_horizon_months: 1
  temporal_model:
    minimum_consecutive_pairs: 3
    maximum_scalar_coefficient: 0.99
  process_noise:
    quantile: 0.95

training:
  initial_learning_rate: 0.001
  final_learning_rate: 0.00001
  batch_size: 256
  maximum_epochs: 30
  early_stopping_patience_epochs: 5
  validation_fraction: 0.10

identification:
  minimum_support_per_class: 200
  minimum_control_transition_replicates: 3
  uncertainty:
    bootstrap_resamples: 500
  nuisance_rank:
    candidates: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    maximum: 20
    bootstrap_resamples: 200
    minimum_bootstrap_stability_fraction: 0.80
  eigengap_ratio:
    candidates: [1.05, 1.10, 1.25, 1.50, 1.75, 2.00]
    default_without_nested_calibration: 1.25
  target_coverage:
    candidates: [0.80, 0.85, 0.90, 0.95]
    primary: 0.90
  control_span_violation:
    primary_alpha: 0.05
    sensitivity_alpha: [0.01, 0.05, 0.10, 0.20]
  private_contamination:
    primary_alpha: 0.05
    sensitivity_alpha: [0.01, 0.05, 0.10, 0.20]
    minimum_history_residuals: 5
  historical_plausibility_radius:
    center_norm_quantile: 0.95
    minimum_reference_centers: 5
    sensitivity_multipliers: [0.75, 1.00, 1.50, 2.00]
  covariance_regularization:
    primary_c: 0.01
    sensitivity_c: [0.001, 0.01, 0.05, 0.10]
  control_reconstruction_gate:
    held_out_residual_quantile: 0.75
    minimum_pass_fraction: 0.80
  tail_diagnostic:
    maximum_absolute_excess_kurtosis: 10.0
    maximum_flagged_coordinate_fraction: 0.10

certification:
  alignment_threshold:
    percentile_candidates: [50, 60, 70, 75, 80, 85, 90]
  ambiguity_width:
    percentile_candidates: [50, 60, 70, 75, 80]
  forecast_set_diameter_abstention:
    historical_realized_diameter_quantile: 0.90
  leave_one_client_out_stability:
    minimum_unchanged_fraction: 0.80
  random_matching:
    minimum_exact_or_source_fraction: 0.80

operators:
  minimum_valid_coverage: 0.50
  maximum_composed_atomic_actions: 3
  validation:
    execution_timeout_seconds: 60
    android_monkey_events: 500
    minimum_behavior_jaccard: 0.80

ablations:
  zero_control_span_violation_budget: 0
  zero_private_contamination_budget: 0

hardening:
  weight:
    candidates: [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    maximum_clean_fnr_degradation_percentage_points: 2.0
  maximum_actions_per_sample:
    candidates: [1, 3, 5, 10]
    primary: 5

baselines:
  point_ridge_relative: 0.001

robustness:
  corrupted_client_allowance:
    counts: [0, 1, 2]
    attacks:
      - basis_rotation
      - false_rank_reporting
      - beta_under_reporting
      - transition_poisoning
      - fabricated_complementarity
    parameters:
      basis_rotation_degrees: 30
      false_rank_increment: 2
      beta_multiplier: 0.50
      transition_poisoning_sigma: 2.0
      fabricated_complementarity_rotation_degrees: 45
  real_stress:
    control_support_fractions: [0.75, 0.50, 0.25]
    control_transition_noise_sigma_multipliers: [0.25, 0.50, 1.0]

statistics:
  confidence_level: 0.95
  minimum_paired_cutoffs: 6
  maximum_missing_cutoff_fraction: 0.10
  bootstrap:
    resamples: 10000
  wilcoxon:
    maximum_nonzero_pairs_for_exact: 25
  multiplicity:
    q: 0.05
  minimum_material_effects:
    early_horizon_fnr_absolute_reduction_percentage_points: 2.0
    action_certification_precision_absolute_increase: 0.05
    maximum_coverage_deficit_absolute: 0.02

seeds:
  representation: [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
  detector_training: [2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010]
  synthetic_generation: [3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010]
  synthetic_noise: [4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008, 4009, 4010]
  operator: [5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010]
  calibration: [6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6010]
  baseline: [7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008, 7009, 7010]
  analysis: [8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010]
  client_selection: [9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010]

synthetic:
  base_sigma: 1.0
  shared_transition_norm_over_sigma: 1.0
  independent_draws_per_grid_cell: 30
  nested_noise_draws_per_seed: 3
  defaults:
    nuisance_dimension_fraction: 0.30
    control_malicious_amplitude_ratio: 1.0
    pairwise_principal_angle_degrees: 45
    common_intersection_dimension: 2
    federation_client_count: 3
    federation_geometry: complementary
    control_sample_size: 200
    malicious_sample_size: 100
    control_span_violation_over_sigma: 0.10
    synchronized_nuisance_over_sigma: 0.0
    private_transition_norm_over_sigma: 0.25
    private_transition_sparsity_mode: dense
    outlier_client_count: 0
    spectral_conditioning_ratio: 0.10
    action_rotation_angle_degrees: 30
  sweeps:
    nuisance_dimension:
      fractions: [0.05, 0.15, 0.30, 0.50, 0.70]
    control_malicious_amplitude_ratio: [0.25, 0.50, 1.0, 2.0, 4.0]
    pairwise_principal_angle_degrees: [0, 15, 30, 45, 60, 90]
    common_intersection_dimension: [0, 2, 5, 10]
    federation:
      client_counts: [2, 3, 5, 8]
      geometries: [redundant, complementary]
      matched_total_samples: true
    control_sample_size: [50, 100, 200, 500, 1000]
    malicious_sample_size: [20, 50, 100, 200, 500]
    control_span_violation_over_sigma: [0, 0.10, 0.25, 0.50, 1.0]
    synchronized_nuisance_over_sigma: [0, 0.25, 0.50, 1.0, 2.0]
    private_transition:
      norm_over_sigma: [0, 0.25, 0.50, 1.0, 2.0]
      sparsity_modes: [dense, ten_percent_sparse]
      sparse_fraction: 0.10
    outlier_client_stress:
      corrupted_client_counts: [0, 1, 2]
      attacks: [rotation, rank_misreport, beta_underreport, poisoning, fabricated_complementarity]
    spectral_conditioning_ratio: [0.01, 0.05, 0.10, 0.50, 1.0]
    action_rotation_angle_degrees: [0, 15, 30, 45, 60, 75, 90]

client_selection:
  budget_fractions: [0.25, 0.50, 0.75]
  d_optimal_ridge: 1.0e-6

numerical:
  scale_standardization_floor: 1.0e-8
  rank_clip_epsilon_relative: 1.0e-6
  zero_displacement_floor: 1.0e-10
  projection_tie_tolerance: 1.0e-9
  condition_number_limit: 1.0e+8
  solver:
    relative_tolerance: 1.0e-8
    absolute_tolerance: 1.0e-8
    duality_gap_tolerance: 1.0e-8
    maximum_iterations: 200

reporting:
  significant_figures:
    percentages_and_rates: 3
    raw_action_width_and_alignment: 4
    effect_sizes_and_p_values: 3
  p_value_display_threshold: 1.0e-4

artifacts:
  configuration_file: configs/fedact.yaml
  outputs_root: outputs
  results_root: results
  directories:
    preprocessing: outputs/preprocessing
    shared_artifacts: outputs/artifacts
    shared_models: outputs/artifacts/models
    shared_scores: outputs/artifacts/scores
    shared_fitted: outputs/artifacts/fitted
    shared_baselines: outputs/artifacts/baselines
    shared_derived: outputs/artifacts/derived
    shared_provenance: outputs/artifacts/provenance
    experiments: outputs/experiments
    cache: outputs/cache
    staging: outputs/cache/staging
    result_experiments: results/experiments
    project_summary: results/project_summary
    reproducibility: results/project_summary/reproducibility
  experiment_directories:
    - math-verification
    - synthetic-geometry
    - action-certificate-validation
    - prospective-evaluation
    - ablations
    - federation
    - failure-boundaries
    - cross-corpus
    - client-selection
    - statistical-synthesis
  result_payload_directories: [figures, tables, metrics, statistics]
  active_artifact_index: outputs/artifacts/provenance/indexes/artifact_index.jsonl
  dependency_index: outputs/artifacts/provenance/indexes/dependency_index.json
  evidence_index: results/project_summary/reproducibility/execution/evidence_index.json
```

## Configuration-linked scientific definitions

### Target coverage and simultaneous uncertainty allocation

The selected target coverage \(p\) defines the client-level simultaneous bootstrap allocation in §8.2. Control-span/private-transition residual allowances use their independently selected alpha candidates. Known-truth calibration in §25 verifies the resulting complete-set/action coverage rather than assuming the component quantiles compose exactly in finite samples.

### Historical plausibility set

The historical feasible set is the L2 plausibility ball intersected with the client ellipsoidal cylinders in §8.3. The base radius is derived only from strictly earlier minimum-norm control-compatible points, so radius construction never depends on the very radius it is defining.

### Temporal set center and process error

The set center is the Euclidean Chebyshev center defined in §8.3. Temporal dynamics are the scalar \(A=aI\) model, and process error is the configured quantile of one-step residual norms \(\|\hat g_{u+1}-a\hat g_u\|_2\).

### Later-real transition proxy

For cutoff \(T\), cohort \(c\), and horizon \(h\), define pre/post malicious means independently for every eligible client:

\[
\hat\mu^{M,pre}_{k,c,T,h} =
\mathrm{mean}\lbrace E_T(x):x\in c,\;t\in[T-h,T)\rbrace,
\]

\[
\hat\mu^{M,post}_{k,c,T,h} =
\mathrm{mean}\lbrace E_T(x):x\in c,\;t\in[T,T+h)\rbrace.
\]

Each side must satisfy the same malicious support floor. Let

\[
d_{k,c,T,h} =
\hat\mu^{M,post}_{k,c,T,h} -
\hat\mu^{M,pre}_{k,c,T,h},
\]

\[
m_{k,c,T,h} =
\left(
\frac1{n^{pre}_{k,c,T,h}}
+
\frac1{n^{post}_{k,c,T,h}}
\right)^{-1}.
\]

The later-real proxy is the effective-support-weighted pooled displacement

\[
\boxed{
\hat g^{real}_{c,(T,T+h]} =
\frac{\sum_km_{k,c,T,h}d_{k,c,T,h}}
{\sum_km_{k,c,T,h}}.
}
\]

No client control subtraction is applied to this evaluation proxy. Its known bias remains residual nuisance and pooled private transitions because the true latent shared transition is unobserved. The definition applies identically to every configured horizon and resolves the endpoint semantics without shortening intervals.

### Dataset-observed-value rule

The loaders validate documented source expectations but record and use the acquired release's actual schema, counts, feature identities, timestamp granularity, and supported semantic fields under §10. A missing semantic field narrows eligibility; it is never synthesized.

### Sensitivity policy

Required sensitivity dimensions remain control-span violation, private contamination, historical plausibility radius, alignment/ambiguity thresholds, horizon, nuisance rank, target coverage, control support, and action geometry. Sensitivity results may not replace the primary confirmatory analysis.

### Infeasible-intersection semantics

If \(\mathcal G_{c,t}=\varnothing\), the outcome remains `INFEASIBLE`. The minimum uniform radius inflation \(\kappa\) is diagnostic only and never becomes the analysis-facing set.

### Challenge-selection semantics

The fixed greedy action-selection and deterministic tie rules are defined in §8.3. The cap comes from `hardening.maximum_actions_per_sample`.

### Baseline implementation identity

External comparator code identities are acquired and recorded according to §14. A comparator is not approximated when its required method definition is unavailable.

# PART II — EXECUTION PIPELINE

# 19. Scientific Workflow and Execution Order

## 19.1 Dependency order

```text
Scientific and configuration authority
        ↓
Mathematical and numerical verification
        ↓
Synthetic generator smoke validation
        ↓
Synthetic theory and geometry validation
        ↓
Real-data feasibility and control audit
        ↓
Baseline reproduction and parity validation
        ↓
Nested pre-cutoff calibration
        ↓
Real-data action-certificate validation
        ↓
Main prospective FedACT evaluation
        ↓
Novelty-critical ablations
        ↓
Federation and complementarity evaluation
        ↓
Robustness and failure-boundary evaluation
        ↓
Cross-corpus generalization
        ↓
Optional communication-limited client selection
        ↓
Statistical synthesis
        ↓
Manuscript evidence generation
```

The dependency order is fixed. Real-data feasibility, baseline parity, and nested calibration are automatic prerequisites of downstream real-data workflows rather than separate operator-facing research commands. Communication-limited client selection is optional and does not block statistical synthesis.

## 19.2 Shared execution requirements

Every scientific workflow inherits:

* chronology rules in §9;
* baseline fairness in §14.4;
* statistical protocol in §17;
* the Configuration YAML;
* provenance, artifact-validity, deterministic-execution, and selective-invalidation contracts in §§34 and 38–40.

Scientific decisions are determined by this roadmap/configuration and may not be redefined interactively after the affected later-real outcomes are inspected.

A workflow records:

* scientific purpose;
* required upstream artifacts;
* manipulations/comparators;
* metrics;
* applicable statistical analysis;
* scientific outcome;
* resulting artifacts.

Scientific outcomes are:

```text
PASS
FAIL
INSUFFICIENT_EVIDENCE
INFEASIBLE
NUMERICAL_FAILURE
ASSUMPTION_VIOLATION
ABSTENTION_EXPECTED
```

Infrastructure/runtime failure remains separate.

A later workflow failure never invalidates an already-complete upstream artifact merely because the later workflow failed. Upstream artifacts remain reusable until one of their material dependencies changes.

## 19.3 Execution and artifact dependency spine

```text
inputs
→ dataset preparation
→ cutoff-safe preprocessing and splits
→ representation / detector / baseline training
→ immutable encoding, scoring, transition summaries, and action displacements
→ nested calibration / set construction / action certification
→ prospective evaluation and ablation/federation/failure-boundary outcomes
→ statistical analysis
→ figures, tables, compact metrics/statistics evidence, and reporting
```

For FedACT, the calibration boundary consists of nested pre-cutoff calibration, uncertainty and plausibility-set parameters, temporal-set construction, action support intervals, \(\tau_{align}\), \(\tau_{amb}\), decision states, and certificates.

Every artifact belongs to one producer boundary. Downstream workflows consume immutable artifact identities rather than reconstructing equivalent upstream work independently.

| Boundary | Principal reusable artifacts | Typical downstream consumers |
| --- | --- | --- |
| Inputs | raw-data identity/checksum, authoritative configuration subsets, operator source assets | all later boundaries |
| Dataset preparation | parsed canonical records, schema/data-quality manifest, source chronology fields | cutoff/split construction, all real-data workflows |
| Preprocessing and splits | cutoff manifests, train/validation/test splits, client/cohort manifests, fitted preprocessing transforms, eligible operator/sample indices | training, controls, calibration, evaluation |
| Training/checkpoints | cutoff-fixed representation checkpoint, base detector checkpoint, independently fitted baseline checkpoints | scoring, transitions, hardening, evaluation |
| Scoring and summaries | encoded samples, detector scores/predictions, malicious/control transition summaries, nuisance bases/constraints, action displacements | calibration, feasible sets, intervals, baselines |
| Calibration and certification | nested calibration result, temporal model/process-error set, historical/prospective feasible sets, action intervals, decisions, certificates/abstentions | main evaluation, ablations, federation, failure boundaries, cross-corpus |
| Evaluation | per-cutoff/per-seed metrics, exposure curves, comparator outcomes, diagnostics | statistical synthesis |
| Analysis | paired contrasts, bootstrap objects, tests, multiplicity results, sensitivity summaries, claim-state inputs | reporting |
| Reporting | figures, tables, presentation-formatted values, compact metrics/statistics evidence, reproducibility evidence, evidence index | manuscript only |

## 19.4 Experiment-to-artifact map

| Experiment / audit | Consumes / may reuse | Produces | Downstream consumers |
| --- | --- | --- | --- |
| Exact Population Identified-Set Verification | configuration, analytical cases | exact-set verification result, residual diagnostics | mathematical verification completion |
| Functional Identifiability Verification | analytical geometry cases | functional-identifiability result | mathematical verification, synthetic geometry |
| Action-Width Bound Verification | analytical cases, support solver | bound-comparison result | mathematical verification, spectral sweep |
| Constraint-Monotonicity Verification | nested analytical sets | monotonicity result | mathematical verification |
| Support-Solver Verification | solver configuration, analytical sets | solver accuracy/feasibility result | all set/action-support workflows |
| Degenerate Action-Displacement Rejection | immutable test encoder fixture, operators | rejection result | operator/action workflows |
| Infeasible-Set Handling Verification | contradictory analytical constraints | infeasibility-handling result | all feasible-set workflows |
| Synchronized-Nuisance Non-Identification Verification | analytical equivalent decompositions | non-identification verification result | failure-boundary interpretation |
| Synthetic Generator Smoke Validation | generator/config, smoke seeds | smoke manifest and correctness results | synthetic geometry |
| Synthetic Theory and Geometry program | generator artifacts, sweep grid | known-truth sweep metrics/source data | synthesis and figures |
| Real-Data Feasibility and Control Audit | acquired corpora, cutoff-safe preparation | chronology/support/control/client/operator/representation manifests | all real-data workflows |
| Baseline Reproduction and Parity | prepared data, analytical/synthetic fixtures as applicable | baseline checkpoints/parity manifests | confirmatory comparisons |
| Nested Pre-Cutoff Calibration | inner pseudo-futures and compatible upstream artifacts | selected calibration result and manifest | all prospective real-data workflows |
| Real-Data Action-Certificate Validation | calibrated sets, action displacements, later-real observations | action-group outcomes and certificate metrics | prospective interpretation, synthesis |
| Main Prospective FedACT Evaluation | compatible trained/scored/calibrated artifacts | hardened checkpoints, comparator outcomes, exposure/predictive metrics | ablations/federation/failure workflows, synthesis |
| Novelty-Critical Ablations | compatible prospective artifacts with only declared boundary changed | ablation outcomes | mechanism synthesis |
| Federation and Complementarity | compatible client/control artifacts | federation contrasts and diagnostics | federation synthesis |
| Robustness and Failure Boundaries | compatible base artifacts plus declared stress manipulation | boundary curves and diagnostics | limitation synthesis |
| Cross-Corpus Generalization | EMBER2024 compatible artifacts | cross-corpus evidence | synthesis |
| Optional Client Selection | compatible federation constraints/actions | budget-matched selection outcomes | optional synthesis/reporting |
| Statistical Synthesis | verified full-precision outcomes | paired contrasts, intervals, multiplicity, sensitivity and claim-state inputs | reporting |

Where multiple rows consume the same upstream artifact, they reference the same immutable artifact identity when its dependency fingerprint matches. They may not independently retrain, rescore, or recalibrate merely because they belong to different workflows.

## 19.5 Artifact lifecycle and completion rule

Every reusable artifact has exactly one lifecycle:

```text
planned → staging → complete/valid → reused
                    ↘ stale → replaced/cleaned
staging/failed → incomplete → cleaned
```

Only `complete/valid` artifacts may be consumed. An artifact becomes complete only after all required files, manifest fields, integrity checks, and scientific invariants for that boundary succeed and a completion record is atomically committed. A directory/checkpoint/metrics file without that completion record is never reusable.

# 20. Mathematical and Numerical Verification

## Experiments

### Exact Population Identified-Set Verification

Construct exact low-dimensional projector systems and verify

\[
\mathcal G^*=g_0+\ker(A).
\]

### Functional Identifiability Verification

Construct cases with an unresolved full state and action directions both inside and outside \(\mathrm{range}(A^\top)\). Verify the equivalence in §7 exactly.

### Action-Width Bound Verification

For analytically solvable stacked L2 systems, compare numerical support width with

\[
2\epsilon\sqrt{q^\top H^\dagger q}.
\]

### Constraint-Monotonicity Verification

For nested sets \(\mathcal G^+\subseteq\mathcal G\), verify

\[
L_o^+\ge L_o,
\qquad
U_o^+\le U_o.
\]

### Support-Solver Verification

The support/feasibility solver is CVXPY with ECOS. Cross-problem warm starts are disabled. The implementation passes the values under `numerical.solver` to ECOS's relative, absolute, feasibility/duality, and iteration-limit options.

Accepted terminal states are:

* `optimal` for a solved support/center/feasibility problem;
* a solver-certified infeasible state when infeasibility is the scientific outcome being tested.

`optimal_inaccurate`, unresolved inaccurate states, solver exceptions, iteration exhaustion, nonfinite primal/dual values, or a returned solution violating the requested feasibility tolerance are `NUMERICAL_FAILURE`.

For boxes, L2 balls, ellipsoids, projector cylinders, and their analytically solvable intersections:

* compute closed-form support where available;
* compare both numerical minima and maxima;
* verify primal feasibility;
* verify objective error is within `max(relative_tolerance*|closed_form|, absolute_tolerance)`.

### Chebyshev-Center Verification

Verify the §8.3 center against analytical balls, boxes, and symmetric intersections, including the minimum-norm tie rule.

### Diameter-Bound Verification

For analytically solvable sets, verify that

\[
\mathrm{diam}(\mathcal G)\le D_{\mathrm{box}}(\mathcal G)
\]

and that the coordinate support extrema satisfy the numerical solver tolerances.

### Degenerate Action-Displacement Rejection

Verify that an action satisfying

\[
E_T(o(x))=E_T(x)
\]

is deterministically rejected by the configured zero-displacement rule.

### Infeasible-Set Handling Verification

Construct contradictory constraints and verify that the scientific set remains infeasible, while the minimum uniform inflation factor is emitted only as a diagnostic.

### Synchronized-Nuisance Non-Identification Verification

Construct two observationally equivalent decompositions of shared threat and synchronized residual nuisance and verify identical permitted observations with different latent decompositions.

## Primary metrics

* analytical-versus-numerical absolute and relative error;
* feasibility residual;
* support-bound ordering;
* center agreement;
* diameter upper-bound validity;
* decision-state agreement.

## Completion criterion

Every mathematical identity and solver behavior required by the executable FedACT path must pass before later set/certificate workflows can run. An unresolved support, center, diameter, or infeasibility error blocks those descendants.

# 21. Synthetic Generator Smoke Validation

## 21.1 Generator scale and randomness

The synthetic representation dimension is \(d=64\).

Let

\[
\sigma=\texttt{synthetic.base＿sigma}.
\]

The shared transition is generated by drawing \(v\sim\mathcal N(0,I_d)\) and setting

\[
g=
\sigma\,
\texttt{synthetic.shared＿transition＿norm＿over＿sigma}
\frac{v}{\|v\|_2}.
\]

The 30 independent structural/noise realizations for each grid cell are generated exactly as follows. For seed index \(i=0,\ldots,9\), pair `seeds.synthetic_generation[i]` with `seeds.synthetic_noise[i]`, construct one NumPy `SeedSequence` from that integer pair, and spawn `synthetic.nested_noise_draws_per_seed` child streams. The resulting \(10\times3=30\) child streams are the `synthetic.independent_draws_per_grid_cell` realizations. The same structural child identity is reused across paired conditions of a sweep so only the manipulated factor changes.

Unless a factor is being swept, use the corresponding value under `synthetic.defaults`; no median or implementation-chosen default is permitted.

## 21.2 Nuisance spaces

Convert a nuisance-dimension fraction \(f\) to

\[
r=\max\lbrace1,\min(d-1,\lfloor fd+0.5\rfloor)\rbrace.
\]

A random orthonormal basis is produced by QR decomposition of a standard-normal matrix with deterministic column signs chosen so the largest-magnitude entry in each column is positive.

For **redundant** geometry, all clients share the same nuisance basis.

For **complementary** geometry with requested common-intersection dimension \(d_0\):

1. draw one common orthonormal basis \(U_0\) of dimension \(\min(d_0,r)\);
2. construct each client's remaining \(r-d_0\) basis vectors from the orthogonal complement of \(U_0\);
3. for a requested pairwise principal-angle setting \(\theta\), rotate the client-specific blocks toward/away from a shared reference block using \(\cos\theta\) and \(\sin\theta\), then re-orthogonalize;
4. reject and regenerate from the same deterministic child stream sequence until numerical SVD verifies the requested intersection dimension and the non-common principal angles within `numerical.projection_tie_tolerance`.

For \(K>2\), client-specific complementary blocks are placed cyclically in the available orthogonal complement; if the requested \((K,r,d_0)\) combination cannot fit in \(d\), that grid cell is `NOT_GEOMETRICALLY_FEASIBLE` rather than silently changing rank.

## 21.3 Control observations and transition replicates

For client \(k\), each control replicate \(j\) is generated as

\[
b_{k,j}=U_ka^B_{k,j}+\epsilon^B_{k,j},
\]

\[
a^B_{k,j}\sim
\mathcal N(0,\sigma_B^2I_r),
\qquad
\epsilon^B_{k,j}\sim
\mathcal N(0,\sigma^2I_d).
\]

The malicious nuisance amplitude is \(\sigma_M=\sigma\). The swept control/malicious amplitude ratio \(r_{BM}\) sets

\[
\sigma_B=r_{BM}\sigma_M.
\]

When a control sample-size condition specifies \(n_B\), the generator creates the corresponding two-window sample means explicitly from \(n_B\) observations per side before forming each transition replicate. The number of distinct historical control-transition replicates is the maximum of `identification.minimum_control_transition_replicates` and the number required by the historical window/cutoff cadence.

## 21.4 Malicious transition

For each client,

\[
y_k =
g
+
U_ka_k
+
r_k
+
\ell_k
+
s
+
\epsilon_k.
\]

Generate

\[
a_k\sim\mathcal N(0,\sigma_M^2I_r).
\]

### Control-span violation

Draw a unit vector \(v_{r,k}\) in the orthogonal complement of \(\mathcal N_k\) and set

\[
r_k=
\alpha_r\sigma v_{r,k},
\]

where \(\alpha_r\) is the selected `control_span_violation_over_sigma`.

### Synchronized residual nuisance

Draw one unit vector \(v_s\) in the orthogonal complement of the span of all client nuisance bases when such a direction exists, and set

\[
s=\alpha_s\sigma v_s.
\]

If the requested geometry has no such nonzero direction, the synchronized-nuisance condition is `NOT_GEOMETRICALLY_FEASIBLE`.

### Private transition

For dense private transition, draw a standard-normal vector, normalize it, and scale it to \(\alpha_\ell\sigma\).

For `ten_percent_sparse`, choose exactly

\[
\max\lbrace1,\lfloor
\texttt{synthetic.sweeps.private＿transition.sparse＿fraction}\,d+0.5
\rfloor\rbrace
\]

coordinates without replacement using the structural stream, draw standard-normal values on those coordinates, normalize, and scale to \(\alpha_\ell\sigma\).

### Malicious sampling noise

For \(n_M\) observations on each side of a transition, the mean-displacement sampling noise is drawn as

\[
\epsilon_k\sim\mathcal N\left(0,\frac{2\sigma^2}{n_M}I_d\right).
\]

The generator also materializes the corresponding per-side sample populations when a workflow requires the bootstrap estimator rather than only the sufficient transition statistic.

## 21.5 Spectral conditioning

The spectral-conditioning sweep constructs the stacked projected system in an orthonormal reference basis and scales its nonzero singular values so that

\[
\frac{\sigma_{\min}^2(A)}{\sigma_{\max}^2(A)}
\]

equals the configured `spectral_conditioning_ratio`, while preserving the requested nullspace. The transformed client projectors are then validated against the intended \(H=A^\top A\) spectrum before the draw is accepted.

## 21.6 Action geometry

Let \(q_{\mathrm{range}}\) be a unit vector in \(\mathrm{range}(A^\top)\) and \(q_{\mathrm{null}}\) a unit vector in \(\ker(A)\), drawn deterministically and orthogonalized.

For action-rotation angle \(\theta\),

\[
q(\theta) =
\cos(\theta)q_{\mathrm{range}}
+
\sin(\theta)q_{\mathrm{null}}.
\]

When one of the required subspaces is zero-dimensional, the corresponding grid cell is marked `NOT_GEOMETRICALLY_FEASIBLE`.

True action score is

\[
q^\top g.
\]

## 21.7 Required generator outputs

Each generated realization returns:

```text
g
U_k
a_k
r_k
ell_k
synchronized_residual
epsilon_k
P_k
control_observations
control_transition_replicates
malicious_side_observations
common_nullspace
stacked_A
H
q_o
true_action_scores
structural_seed_identity
noise_seed_identity
grid_cell_identity
```

## 21.8 Smoke validation

Verify:

* exact nuisance dimensions and orthonormality;
* requested common-intersection dimension;
* requested principal angles;
* redundant/complementary geometry;
* control/malicious amplitude ratio;
* residual/private/synchronized nuisance norms;
* sparse private support size;
* requested spectral-conditioning ratio;
* action rotation;
* deterministic replay;
* known-truth feasible-set construction;
* action intervals and states;
* hardening integration;
* artifact generation.

Smoke validation supports implementation correctness only and is not scientific effectiveness evidence.

# 22. Synthetic Theory and Geometry Validation

All primitive sweep values are read from `synthetic.sweeps`; every unswept factor uses `synthetic.defaults`. Generator mechanics and seed mapping are fixed by §21.

### Nuisance-Dimension Sweep

Manipulate:

\[
\frac{r_k}{d}
\]

With the fixed representation dimension (d=64), the configured nuisance-dimension fractions map to the exact integer nuisance dimensions 3, 10, 19, 32, and 45 in the same order. These integer dimensions are derived experiment values, not separate configuration entries.

Hold fixed:

* total samples;
* noise;
* action geometry;
* control-span validity.

**Expected:** larger nuisance spaces enlarge latent ambiguity only when added unresolved dimensions affect the relevant action.

### Control/Malicious Amplitude-Mismatch Sweep

Manipulate the ratio between benign-control and malicious nuisance amplitudes.

Compare:

* FedACT;
* matched benign subtraction;
* projected point methods.

**Expected:** subtraction degrades as amplitude mismatch increases; control-subspace/set methods remain calibrated when nuisance directions remain valid.

### Principal-Angle Geometry Sweep

Manipulate principal angles among nuisance spaces while holding ranks and total samples fixed.

Measure:

* global spectral diagnostics;
* action widths;
* certification state.

**Key test:** action benefit should depend on action-specific contraction, not pairwise geometry alone.

### Common-Intersection Partial-Identification Sweep

Manipulate:

\[
d_0=\dim\left(\bigcap_k\mathcal N_k\right).
\]

Generate actions:

* orthogonal to the common intersection;
* partially overlapping;
* primarily inside it.

**Critical evidence:** full transition remains unresolved while some actions remain identified.

### Redundant versus Complementary Synthetic Federation

Compare equal-total-sample systems:

```text
redundant client geometry
vs
complementary client geometry
```

Measure:

* action width;
* ambiguity;
* certification;
* point-estimation error.

This separates replication gain from identification gain.

### Control-Sample-Size Sweep

Manipulate \(n_k^B\).

Measure:

* subspace estimation error;
* action width;
* coverage;
* eigengap interactions.

### Malicious-Sample-Size Sweep

Manipulate \(n_k^M\).

Expected:

* mean-transition error contracts;
* structural action ambiguity remains.

### Control-Span-Violation Sweep

Increase:

\[
\|P_kr_k\|_2.
\]

Compare:

* calibrated uncertainty;
* the no-span-violation allowance ablation.

Expected:

```text
correct allowance
→ preserved coverage
→ wider intervals
→ lower certification

understated allowance
→ undercoverage
→ false certification
```

### Synchronized-Nuisance Sweep

Set:

\[
r_k=s\qquad\forall k.
\]

with \(s\) outside all nuisance spans.

Expected:

* client count does not solve decomposition;
* complementary controls do not identify \(s\);
* declared sensitivity widens/invalidates certificates.

### Private-Transition Sweep

Inject independent/sparse \(\ell_k\).

Expected:

* inconsistency/widening without private allowance;
* strong private modes reduce validity of global claims;
* local-only method may become more appropriate.

### Outlier-Client Stress Test

Use the configured corrupted-client counts 0, 1, and 2. For a synthetic population of size \(K\), their corresponding corrupted-client fractions are derived as \(0\), \(1/K\), and \(2/K\); these expressions are not configuration values.

Stress:

* nuisance-basis rotation;
* false rank;
* uncertainty under-reporting;
* transition poisoning;
* fabricated complementarity.

Primary output:

* leave-one-client-out certificate instability;
* infeasibility;
* robustness limitations.

No Byzantine-security claim is allowed.

### Spectral-Conditioning Sweep

Manipulate the smallest positive eigenvalue while holding the action nullspace component fixed.

Compare:

\[
\kappa_{act}(q;H)
\]

with exact interval width.

### Action-Specific versus Global Identification

Hold \(H\) fixed.

Rotate \(q\) from identifiable range toward nullspace.

Required pattern:

```text
global rank unchanged
global spectrum unchanged
action interval widens
certification state changes
```

This is a central FedACT mechanism test.

## Completion criterion

Must establish:

1. feasible-set calibration under declared assumptions;
2. action-functional behavior consistent with theory;
3. existence of transition-unresolved/action-resolved state;
4. matched-sample complementarity effect;
5. synchronized-nuisance impossibility.

Failure of items 2–3 blocks the central contribution.

---

# 23. Real-Data Feasibility and Control Audit

Executed automatically by `fedact preprocess` for each real corpus.

### Real-Data Chronology Audit

Verify:

* timestamp semantics;
* first-seen semantics where applicable;
* ordering completeness;
* no future-derived labels in historical operations.

Output: cutoff manifest.

### Real-Data Support Audit

For each candidate cutoff/cohort/client:

* malicious count;
* control count;
* number of control strata;
* temporal overlap;
* operator-eligible sample count.

### Real-Data Control Audit

Evaluate:

* matched context support;
* held-out control-transition reconstruction;
* nuisance-rank stability;
* eigengap;
* source-stratified residuals.

### Real-Data Client-Semantics Audit

Classify each client definition as:

* natural organization;
* natural source or sensor;
* diagnostic partition;
* synthetic partition.

Allowed claims depend on the classification.

### Real-Data Operator Audit

Verify:

* action executability;
* semantic preservation;
* zero-displacement frequency;
* per-cohort action coverage.

### Real-Data Representation Audit

Verify:

* cutoff-only training;
* cutoff-fixed encoder hash;
* stable preprocessing;
* no future normalization.

## Dataset eligibility outcome

Each dataset is classified as:

* eligible for primary evidence;
* eligible for secondary evidence;
* diagnostic only;
* unusable for the intended evidence.

A dataset missing natural client identities may still support action-mechanism evidence but not strong natural-federation claims.

---

# 24. Baseline Reproduction and Parity Validation

Executed automatically as a fitted-artifact dependency the first time a downstream workflow requires baseline comparators.

## Required validation

For every baseline used later, confirm:

```text
same cutoff
same historical information
same representation where applicable
same detector architecture where applicable
same valid operator library
same number of injected hardening samples where applicable
same evaluation horizon
no additional future access
fair adaptation budget
```

### Identification-Baseline Parity Validation

Validate all identification comparators against analytical/synthetic cases.

### Security-Baseline Parity Validation

Validate temporal/security baselines on chronological training/evaluation.

### Federation-Baseline Parity Validation

Validate centralized, local, redundant, and complementary implementations.

## Acceptance criteria

A baseline enters confirmatory comparison only after:

* reproducing internally expected behavior;
* passing chronology checks;
* producing deterministic manifests;
* exposing its hyperparameter procedure.

A failed baseline implementation cannot be retained as a deliberately weak comparator.

---

# 25. Nested Pre-Cutoff Calibration

Nested calibration is generated automatically the first time a downstream real-data workflow requires calibrated values for a dataset/external cutoff.

For external cutoff \(T\) and primary horizon \(h_p\), an inner cutoff \(T_i\) is eligible only when:

\[
T_i+h_p\le T
\]

and the full inner historical interval required by §9 is observable without a prohibited chronology gap. Therefore every inner pseudo-future is completely observed before the external cutoff.

Use every eligible inner cutoff at `temporal.cutoff_step_months`. At least `statistics.minimum_paired_cutoffs` inner cutoffs are required; otherwise calibration returns `INSUFFICIENT_EVIDENCE` and the affected prospective execution abstains.

## 25.1 Values varied by nested calibration

The calibration Cartesian product varies only:

* eigengap requirement from `identification.eigengap_ratio.candidates`;
* target coverage from `identification.target_coverage.candidates`;
* control-span alpha from `identification.control_span_violation.sensitivity_alpha`;
* private-transition alpha from `identification.private_contamination.sensitivity_alpha`;
* historical-plausibility radius multiplier from `identification.historical_plausibility_radius.sensitivity_multipliers`;
* alignment percentile from `certification.alignment_threshold.percentile_candidates`;
* ambiguity-width percentile from `certification.ambiguity_width.percentile_candidates`.

Nuisance rank is **derived** inside each candidate by the §8.2 eigengap rule; it is not independently grid-searched.

The following remain fixed during calibration and are not tuned:

* minimum support;
* control-transition replicate requirement;
* control-reconstruction gate;
* rank-stability fraction;
* tail diagnostic;
* temporal model family and fitting rule;
* forecast horizons;
* prospective-set diameter gate;
* operator-coverage gate;
* leave-one-client-out stability fraction;
* primary hardening action cap;
* numerical solver tolerances.

The covariance-regularization primary value is used in confirmatory calibration. Its configured alternative values are sensitivity-only.

## 25.2 Threshold construction inside each candidate

For each inner cutoff:

* the alignment threshold is the selected percentile of the pooled **inner-historical** point-alignment distribution computed from the propagated Chebyshev-center point and valid action directions;
* the ambiguity threshold is the selected percentile of the pooled **inner-historical** FedACT action-width distribution;
* the forecast-diameter threshold is the fixed configured percentile of historical \(D_{\mathrm{box}}\) values;
* all percentiles use the §17 linear quantile rule.

No inner later-real outcome is used to construct a percentile threshold; inner later-real observations are used only to evaluate the candidate.

## 25.3 Candidate validity

A candidate configuration is valid only if all of the following hold over its eligible inner cutoffs:

1. all required client/control/set quality gates are satisfied for enough units to retain at least the minimum paired cutoff count;
2. empirical action-interval coverage against the inner later-real proxy is at least
   \[
   p-\texttt{statistics.minimum＿material＿effects.maximum＿coverage＿deficit＿absolute};
\]
3. false-certification rate is at most \(1-p\);
4. prospective-set diameter, operator coverage, and leave-one-client-out rules are applied exactly as they will be externally;
5. no invalid numerical result is treated as a successful candidate.

Coverage against the inner later-real proxy is a conservative operational calibration check rather than a claim that the proxy equals the latent shared transition. Synthetic known-truth coverage remains the direct estimator-validation evidence.

## 25.4 Deterministic candidate selection

Among valid candidates, select lexicographically by the following objective hierarchy:

1. highest mean inner-cutoff certificate precision;
2. highest mean inner-cutoff certification rate;
3. smallest median inner-cutoff action width;
4. larger realized minimum eligible support;
5. smaller ambiguity-width percentile;
6. lexicographically smallest canonical candidate-configuration hash.

All means first aggregate planned random seeds within cutoff according to §17.3 and then average inner cutoffs equally.

This ordering operationalizes the scientific priorities: validity is a hard gate, false certification is controlled before utility is optimized, and useful selective certification is favored only among valid configurations.

## 25.5 Hardening-weight selection

Hardening weight is selected after the identification/certification candidate above is fixed.

For each configured hardening weight, train/evaluate only on the nested inner histories/pseudo-futures using §8.3. A weight is admissible only when its mean clean FNR degradation is at or below `hardening.weight.maximum_clean_fnr_degradation_percentage_points`.

Among admissible weights, select the weight with the largest mean inner-cutoff absolute early-FNR reduction. Ties within `numerical.projection_tie_tolerance` go to the smaller weight. If no weight is admissible, hardening for that external cutoff returns `INSUFFICIENT_EVIDENCE`; identification/certification may still execute without claiming hardening benefit.

## 25.6 Calibration result

For each dataset/external cutoff record:

```text
outer_cutoff
inner_pseudo_cutoffs
candidate_configurations
candidate_validity
objective_values
selected_configuration
selected_hardening_weight
support_failures
abstentions
seed_values
dependency_fingerprint
producer_code_fingerprint
repository_commit
```

No default value substitutes for failed real confirmatory calibration. `identification.eigengap_ratio.default_without_nested_calibration` is restricted to analytical verification, synthetic smoke, and explicitly diagnostic non-calibrated checks.

# 26. Real-Data Action-Certificate Validation

## Scientific question

Does the FedACT action certificate contain later-real information beyond a point estimate, action validity alone, and random valid augmentation?

## 26.1 Action groups

At each external cutoff/cohort/horizon:

1. **Certified actions** — FedACT-certified under §8.3;
2. **Point-positive ambiguous actions** — FedACT-ambiguous actions whose propagated Chebyshev-center score satisfies
   \[
   q_o^\top\hat g^{pred}_{center}\ge\tau_{align};
\]
3. **Negatively identified actions** — \(U_o<\tau_{align}\);
4. **Matched random valid actions** — sampled from domain-valid nondegenerate candidates without using FedACT interval/point scores.

The propagated point used in group 2 is uniquely the Chebyshev-center point implied by §8.3; no alternative point estimator may be selected post hoc.

## 26.2 Exact later-real relevance

For every action, use §16:

\[
R_o^{real} =
\mathbf1[
q_o^\top\hat g^{real}_{c,(T,T+h]}
\ge\tau_{align}
].
\]

The same pre-cutoff threshold \(\tau_{align}\) defines certificate semantics and later-real relevance.

## 26.3 Matching and random sampling

Let \(N_{cert}\) be the number of certified actions in one cutoff/cohort/horizon.

### Point comparator at matched certification count

To compare precision at a matched certification rate, rank every valid candidate by propagated Chebyshev-center point score descending, with canonical action identity as deterministic tie-breaker, and label the top \(N_{cert}\) point actions as point-selected. Compare their later-real precision with the precision of the \(N_{cert}\) FedACT certificates.

If \(N_{cert}=0\), matched precision is undefined and the cutoff contributes to certification/abstention metrics but not precision inference.

### Matched random valid actions

Sample \(N_{cert}\) candidates without replacement using the applicable `seeds.operator` index. Match in this priority order:

1. same cutoff, cohort, horizon, source sample, and atomic/composed action count;
2. if no unused candidate satisfies all fields, same cutoff, cohort, horizon, and source sample;
3. if still unavailable, same cutoff, cohort, horizon.

Never relax domain validity or horizon. Record the matching level for every selected action.

At least `certification.random_matching.minimum_exact_or_source_fraction` of random matches must satisfy levels 1–2; otherwise that cutoff's certified-vs-random contrast is `INSUFFICIENT_EVIDENCE`.

Execute random matching for every planned operator seed and average the resulting cutoff-level random endpoint before confirmatory inference according to §17.3.

## 26.4 Defensive-effect matching

When an action group is used for hardening, match:

* source training population;
* number of challenges;
* per-sample action cap;
* detector initialization;
* optimization budget;
* clean-cost constraint;
* evaluation horizon.

## 26.5 Outcomes

Primary:

* later-real action alignment;
* certificate precision at the matched certification count.

Secondary:

* Spearman rank alignment between \(L_o\) and later-real alignment;
* action width;
* defensive effect when used.

## 26.6 Required central pattern

Across the prespecified repeated cutoff units:

\[
\text{Certified} >
\text{Point-positive ambiguous} >
\text{Matched random valid}
\]

for prospective relevance, evaluated using the exact inferential/decision rules in §17.

## 26.7 Falsification

The central mechanism is unsupported when the prespecified comparisons show no certificate advantage, point-positive ambiguous actions are equivalently reliable under the decision rules, or matched random valid actions are equivalent/superior. Main prospective evaluation may still execute descriptively, but detector performance alone cannot restore the central certificate claim.

# 27. Main Prospective FedACT Evaluation

## Procedure per cutoff

For each locked \(T_j\):

1. load only cutoff-safe scientific inputs;
2. load the cutoff-fixed representation;
3. construct historical malicious transitions;
4. construct matched controls;
5. estimate client nuisance constraints;
6. intersect constraints into \(\mathcal G_{c,T_j}\);
7. propagate to each locked horizon;
8. generate all cutoff-valid action displacements;
9. solve prospective action intervals;
10. classify positive/negative/ambiguous actions;
11. certify valid actions;
12. abstain where required;
13. harden using certified actions only;
14. complete the hardened checkpoint;
15. expose later-real evaluation observations;
16. evaluate FedACT and all principal baselines;
17. permit reactive baselines to adapt only when their operational information becomes available;
18. record cumulative exposure before adaptation.

## Principal comparators

At minimum:

* static chronological detector;
* strongest temporal-invariance comparator;
* matched benign-subtraction forecasting/hardening;
* projected point reconstruction;
* raw future-transition forecasting;
* random valid mutation;
* static valid-mutation hardening;
* generic matched uncertainty set;
* reactive drift adaptation;
* local-only identification.

Centralized and federation comparators are also evaluated in the federation workflow.

## Primary endpoints

* early-horizon FNR / pre-adaptation exposure;
* action-certification precision.

## Secondary endpoints

* TPR;
* FPR;
* PR-AUC;
* ROC-AUC;
* clean performance degradation;
* certification rate;
* abstention rate;
* interval width;
* time-to-catch-up.

## Success interpretation

Downstream performance supports FedACT only if Real-Data Action-Certificate Validation also supports the action-certification mechanism.

Detector improvement alone cannot establish the central scientific claim.

---

# 28. Novelty-Critical Ablations

Run all applicable ablations on the same external cutoffs and compatible upstream artifacts. An ablation changes only the named scientific boundary.

### Control-Evidence Ablations

**No controls:** replace every client nuisance projector by \(I\), omit control-derived nuisance geometry, and retain the same malicious transition, historical plausibility, temporal, action, and hardening machinery. Sampling uncertainty remains; control-derived \(\rho\) and subspace terms are absent by construction.

**One matched control displacement:** retain exactly one control-transition replicate per client, choosing the eligible replicate with largest effective support \(m_s\); ties use lexical replicate identity. Treat its displacement as the subtraction/projection direction required by this ablation and do not estimate a multidimensional nuisance covariance from it.

These conditions test whether controls and multidimensional nuisance geometry matter.

### Point-versus-Set Ablation

Replace action support intervals with the propagated Chebyshev-center score. A point action is positive when

\[
q_o^\top\hat g^{pred}_{center}\ge\tau_{align}.
\]

Use the matched-certification-count comparison from §26 for false-certification and later-real relevance.

### Global-versus-Action-Specific Identification Ablation

The global gate passes a cohort/horizon only when the nonzero-spectrum condition number of its stacked information matrix satisfies

\[
\kappa^+(H) =
\frac{\lambda_{\max}(H)}{\lambda_{\min}^+(H)}
\le
\texttt{numerical.condition＿number＿limit}.
\]

When the global gate passes, all point-positive domain-valid actions are eligible; when it fails, all abstain. Compare this cohort-level global gate with action-specific FedACT intervals under matched action counts. This uses no separately calibrated global threshold.

### Generic-Robustness Ablation

Use the point estimate plus matched isotropic uncertainty comparator in §14.1 and the random-valid-mutation comparator in §14.2. The isotropic radius is selected only by nested pre-cutoff calibration to match FedACT's certification rate as closely as possible, with ties going to the larger radius.

### Uncertainty-Component Ablations

Starting from the same client summaries, set exactly one of these standardized terms to zero:

* subspace-estimation uncertainty \(u_k^U\);
* control-span allowance \(\rho_k\);
* private-transition allowance \(\xi_k\).

All other uncertainty terms and calibration values remain unchanged. Measure coverage and false-certification consequences.

### Temporal Ablations

**Shuffled history:** within each cutoff/cohort, permute the sequence of historical set centers among their existing time indices using the applicable `seeds.analysis` stream, refit the same scalar temporal model, and keep every non-temporal artifact unchanged.

**No-change dynamics:** set \(a=1\) while retaining the same process-error calibration procedure on residuals \(\hat g_{u+1}-\hat g_u\).

### Action-Mapping Ablation

Within each `(cutoff, cohort, horizon, source_sample, composition_length)` stratum having at least two valid actions, permute the association between action displacement/certificate rank and transformed output artifact using the applicable `seeds.analysis` stream. This preserves domain-valid outputs, source sample, action count, horizon, and training budget while destroying the learned action-support association.

Strata with fewer than two actions are unchanged and excluded from the action-mapping contrast denominator; their counts are reported.

### Width-Gate Ablation

Remove only

\[
W_o\le\tau_{amb}
\]

from the certification rule. Retain the lower-bound threshold, domain validity, set-diameter gate, and leave-one-client-out rule.

### Hardening-Off Ablation

Retain the same certificates and evaluation records but do not optimize the detector head. This separates identification capability from downstream training.

## Claim invalidation

If:

* generic robust training matches FedACT under §17 → identification-driven hardening claim is unsupported;
* point reconstruction matches certificate quality → set-valued decision claim is weakened/unsupported according to the claim map;
* shuffled time matches → prospective temporal claim is unsupported;
* randomized action mapping matches → action-semantic interaction is unsupported;
* controls removed with no effect → control-based identification is unsupported.

# 29. Federation and Complementarity Evaluation

This workflow executes only where at least two quality-eligible clients exist for the relevant condition. LAMDA's default one-client execution is therefore not included unless an acquired release passes §10.2 with a genuine multi-client field.

### Local versus Federated Identification

For every eligible client, construct the complete local FedACT set using only that client and the same historical plausibility rule. Compare each local result with the multi-client intersection on the shared action population.

Aggregate local performance by taking the median local action width/relevance endpoint within cutoff before comparison with the federated endpoint.

Measure:

* action width;
* ambiguity/certification;
* certification precision.

### Redundant versus Complementary Federation

Synthetic execution uses §21 with identical total malicious/control support under `redundant` and `complementary` geometry.

For the real two-source EMBER2024 substrate, the **complementary** condition is the observed Win32/Win64 pair when both pass all gates. The matched **redundant** diagnostic comparator is constructed separately for each source:

1. choose a source with at least twice the support required to create two disjoint pseudo-clients in every required malicious/control cell;
2. deterministically split that source by hash order into two disjoint equal-support pseudo-clients;
3. cap each pseudo-client cell so the combined malicious/control count equals the corresponding combined count used by the observed Win32/Win64 condition;
4. execute the same complete client-estimation and FedACT intersection procedure;
5. when both Win32 and Win64 can supply a redundant pair, compute both source-specific redundant results and average them within cutoff;
6. if neither source has enough support for the matched construction, the real redundant contrast is `NOT_APPLICABLE_INSUFFICIENT_MATCHED_SUPPORT`.

The pseudo-client condition is explicitly a diagnostic matched-redundancy comparator and does not create a natural-client claim.

Primary contrast:

\[
\Delta W_o =
W_o^{redundant} -
W_o^{complementary}.
\]

Positive values favor complementary identification.

Secondary:

* ambiguous-to-certified transitions;
* ambiguous-to-negative transitions;
* later-real action relevance.

### Federated-Summary versus Centralized Equivalence

The centralized-equivalence implementation receives the same raw observations that produced the eligible client summaries, but computes those **same per-client summaries centrally** and then runs the same server intersection. It does not pool clients into one nuisance model.

For deterministic producers, the centrally produced \(\hat U_k,y_k,\hat\Sigma_k,\beta_k\) and resulting action bounds must agree with the federated-summary path within the §20 solver/numerical tolerances. Any discrepancy is an implementation failure, not a scientific effect.

### Randomized Client-Geometry Control

Within each eligible cutoff/cohort, use `seeds.analysis` to permute complete control-derived constraint packages

```text
U_hat
Sigma_hat
beta
eigengap/rank diagnostics
control-quality diagnostics
```

across client malicious transition vectors \(y_k\), while preserving client support counts and the set of transmitted packages. Reconstruct sets/certificates after permutation. This destroys the observed association between each client's transition and its control geometry without changing marginal control geometry or total support.

For \(K=2\), the only non-identity swap is used. For \(K>2\), execute every planned analysis seed and average within cutoff.

## Precision gain versus identification gain

### Precision gain

The unresolved structural subspace is unchanged and uncertainty narrows because of repeated observations.

### Identification gain

A previously unresolved action component becomes constrained by a complementary control view.

These are reported separately.

## Strong federation claim criterion

A strong real-world federation claim is permitted only if:

1. §10.2 classifies the clients as natural organization or natural sensor/source/collection identities with scientifically defensible distinct nuisance processes;
2. control geometry is measurably heterogeneous;
3. complementary information contracts action uncertainty beyond the matched redundant comparator;
4. later-real action quality improves under §17.

Diagnostic platform/source partitions that do not satisfy item 1 may support only a source/format complementarity statement.

# 30. Robustness and Failure-Boundary Evaluation

Every failure-boundary manipulation changes only the named factor while reusing compatible upstream artifacts. Synthetic boundaries use §21 known-truth generation. Real-data stress that cannot be implemented as a genuine observed-world intervention is explicitly summary-level diagnostic evidence and is not interpreted as real attacker behavior.

### Sparse-Control Boundary

Synthetic execution uses the configured control-sample-size sweep.

For real diagnostic stress, deterministically retain `robustness.real_stress.control_support_fractions` of each eligible control cell by hashing `(sample_id, cutoff, fraction)` and taking the smallest hashes. Recompute controls/nuisance/uncertainty from the retained observations. Malicious observations remain unchanged.

Expected:

```text
subspace error ↑
constraint radius ↑
action width ↑
certification ↓
abstention ↑
```

### Weak-Eigengap Boundary

Synthetic execution manipulates nuisance spectra directly.

For real diagnostic stress, add zero-mean Gaussian perturbation to each historical control-transition replicate with per-coordinate scale equal to the median finite coordinate standard deviation of the original control-transition replicates multiplied by each value in `robustness.real_stress.control_transition_noise_sigma_multipliers`. The noise comes from the paired `seeds.analysis` stream. Recompute rank/eigengap and all descendants. This is a sensitivity stress, not an alternative primary estimator.

Expected: client exclusion, rank instability, and/or wider uncertainty.

### Control-Span-Violation Boundary

Synthetic execution uses `synthetic.sweeps.control_span_violation_over_sigma`.

For real data, the prespecified sensitivity is the configured `identification.control_span_violation.sensitivity_alpha` grid; no unobservable true \(r_k\) magnitude is claimed. Compare the primary allowance with more/less conservative quantiles and report coverage-proxy/certificate sensitivity.

### Private-Transition Contamination Boundary

Synthetic execution uses the private-transition norm/sparsity grid in §21.

Real data use only the predeclared `identification.private_contamination.sensitivity_alpha` quantiles of observed historical proxy residuals; no fabricated private malware label is injected into confirmatory real outcomes.

### Synchronized-Nuisance Non-Identification Boundary

Synthetic execution injects the synchronized residual \(s\) from §21 across clients.

Expected interpretation: **fundamental non-identification**. No success claim is permitted.

### Unresolved Action-Geometry Boundary

Use the action-rotation grid from §21 while holding global \(H\) fixed.

Expected:

* interval widening;
* ambiguity;
* abstention.

### Forecast-Horizon Boundary

Use exactly `temporal.forecast_horizons_months` for every source-observable horizon.

Required output:

* \(D_{\mathrm{box}}\);
* action widths;
* certificate rates;
* abstention rates.

### Temporal-Predictability Boundary

Use the existing temporal shuffle and no-change dynamics ablations. No additional stochastic time perturbation is introduced.

### Constraint-Outlier Boundary and Corrupted-Summary Stress

For a realized eligible client count \(K\), form the unique corrupted counts

\[
\mathcal B =
\mathrm{sorted}
\left(
\lbrace0,1,2,\lfloor K/3\rfloor\rbrace
\cap\lbrace0,\ldots,K-1\rbrace
\right).
\]

For each nonzero count, choose corrupted clients by the deterministic permutation generated from the applicable `seeds.analysis` value. Apply exactly one declared corruption family at a time:

* **basis rotation:** rotate the reported leading nuisance basis toward an orthogonal complement by `robustness.corrupted_client_allowance.parameters.basis_rotation_degrees`, then QR-orthonormalize;
* **false rank reporting:** append up to `false_rank_increment` orthogonal basis vectors, clipped at \(d-1\);
* **beta under-reporting:** multiply reported \(\beta_k\) by `beta_multiplier`;
* **transition poisoning:** add a vector of norm `transition_poisoning_sigma` times the median uncorrupted \(\|y_j-\mathrm{GeoMedian}(y)\|_2\), in a deterministic random direction;
* **fabricated complementarity:** rotate the reported nuisance basis away from the dominant uncorrupted pooled nuisance direction by `fabricated_complementarity_rotation_degrees`.

The server receives the corrupted summary as if authenticated; ground-truth corruption identity is used only by the stress evaluator.

Measure:

* set infeasibility;
* leave-one-client-out dependence;
* action-width/certificate changes;
* false certification where ground truth/proxy permits;
* corruption detectability only through the already-declared diagnostics.

Permitted conclusion: sensitivity and limitations under corrupted summaries.

Forbidden conclusion: Byzantine security.

## Failure interpretations

### Graceful abstention

The method recognizes unresolved uncertainty and refuses unsupported action.

### Method failure

Implementation/statistical behavior is incorrect despite assumptions holding.

### Assumption violation

The input regime violates the declared scientific contract.

### Fundamental non-identification

No method using the permitted observations can identify the required distinction.

# 31. Cross-Corpus Generalization

Apply the same FedACT scientific semantics to the acquired EMBER2024 Win32/Win64 subset.

Preserve exactly:

* observation-model interpretation;
* set-valued primary estimand;
* action-functional estimand;
* certification rule;
* chronology and inner-calibration rules;
* statistical protocol;
* claim discipline.

Dataset-specific differences are limited to the observed:

* timestamp granularity;
* client/source semantics;
* context variables and control strata;
* family/cohort availability;
* PE operator eligibility;
* feature schema/preprocessing required by the pinned extractor.

§10 and §9 govern adaptation to the actual acquired release. A documented count or field absent from the acquired data is not invented.

Only external cutoffs and horizons whose complete historical and later-real intervals exist under §9 are run. The configured horizon list is not shortened. If fewer than `statistics.minimum_paired_cutoffs` paired external cutoffs remain, cross-corpus confirmatory inference is `INSUFFICIENT_EVIDENCE` even though descriptive mechanism results may still be reported.

## Generalization claim criterion

A cross-corpus mechanism claim requires:

1. meaningful controls under the observed Win32/Win64 source/format semantics;
2. usable action intervals;
3. prospective certificate association with later-real relevance;
4. graceful uncertainty behavior;
5. downstream hardening effect or an explicitly reported domain-specific null result.

A detector-performance win alone is insufficient. Win32/Win64 evidence may support source/format complementarity but is not described as natural organizational federation.

# 32. Optional Communication-Limited Client Selection

Secondary only.

This workflow runs only for a cutoff/cohort with at least two usable clients.

## 32.1 Candidate action weights

Let \(\mathcal Q\) be the valid candidate action directions available before client selection. Use uniform weights:

\[
\pi_q=\frac1{|\mathcal Q|}.
\]

If \(|\mathcal Q|=0\), the unit is `ABSTENTION_EXPECTED`.

## 32.2 Equal communication budgets

For eligible client count \(K\) and each configured budget fraction \(f\), define

\[
B(f,K)=\max\lbrace1,\min\lbrace K,\lceil fK\rceil\rbrace\rbrace.
\]

Every selector chooses exactly \(B\) clients. Communication is additionally reported using the exact serialized-byte metric in §16 so unequal summary sizes remain visible.

## 32.3 Comparators

### Random

Sample \(B\) clients without replacement using `seeds.client_selection`. Execute all planned selection seeds and average within cutoff as required by §17.3.

### Largest sample count

Rank by malicious effective support

\[
\left(\frac1{n^{M,-}_k}+\frac1{n^{M,+}_k}\right)^{-1}
\]

descending, with lexical client id as tie-breaker.

### Global information selector

Use greedy D-optimal information gain on the whitened client information matrices

\[
H_k =
\hat P_k^\top\hat\Sigma_k^{-1}\hat P_k.
\]

Starting from the empty set, add the client maximizing

\[
\log\det\left(
\lambda I+\sum_{j\in\mathcal K\cup\lbrace k\rbrace}H_j
\right) -
\log\det\left(
\lambda I+\sum_{j\in\mathcal K}H_j
\right),
\]

with \(\lambda=\texttt{client＿selection.d＿optimal＿ridge}\). Ties go to lexical client id.

### Action-interval-contraction selector

Starting from the same empty set, for every remaining client \(k\), construct the candidate feasible set using exactly the same §8 constraints and compute

\[
G_k =
\sum_{q\in\mathcal Q}
\pi_q
\left[
W_q(\mathcal G_{\mathcal K}) -
W_q(\mathcal G_{\mathcal K\cup\lbrace k\rbrace})
\right].
\]

Add the client with largest \(G_k\); ties go to smaller canonical payload bytes then lexical client id. Continue until \(B\) clients are selected.

When \(\mathcal K=\varnothing\), \(\mathcal G_{\mathcal K}\) is the historical plausibility ball alone, so the first-step width is defined.

## 32.4 Primary metrics

Report:

* mean weighted action-width reduction per selected client;
* total weighted action-width reduction;
* reduction per canonical communicated byte;
* certificate-rate/precision consequences secondarily.

The selector does not alter the primary FedACT identification algorithm or become the paper's primary novelty claim.

# PART III — EVIDENCE, REPRODUCIBILITY, AND COMPLETION

# 33. Statistical Synthesis and Sensitivity Analysis

## 33.1 Confirmatory synthesis

Aggregate in the locked hierarchy:

```text
within cutoff
→ across cutoffs
→ within dataset
→ across datasets only where scientifically valid
```

Do not treat multiple actions from the same cutoff as independent top-level replicates.

## 33.2 Required confirmatory contrasts

At minimum:

1. certified vs point-positive ambiguous action relevance;
2. certified vs matched random valid action relevance;
3. FedACT vs principal static/temporal baselines for early exposure;
4. complementary vs redundant federation at matched sample count;
5. full model vs generic uncertainty set;
6. correct temporal order vs shuffle.

## 33.3 Sensitivity analyses

Run locked sensitivity across:

* \(\rho\);
* \(\xi\);
* \(R\);
* \(\tau_{align}\);
* \(\tau_{amb}\);
* horizon;
* nuisance rank;
* coverage level.

Report:

* effect estimate;
* uncertainty;
* certification rate;
* abstention rate;
* clean cost.

## 33.4 Analysis classes

### CONFIRMATORY

Predeclared hypotheses, endpoints, comparisons, statistics.

### SENSITIVITY

Prespecified robustness surfaces around scientific assumptions.

### DIAGNOSTIC

Geometry, eigengap, solver, client influence, residual checks.

### EXPLORATORY

Unexpected patterns not used to redefine confirmatory claims.

Exploratory findings may motivate later work only.

## 33.5 Null results

A null detector effect does not automatically mean the set estimator failed.

A null certification effect directly threatens the central action-identification claim.

All layers must therefore be reported separately.

---

# 34. Reproducibility, Provenance, and Artifact Validity

## 34.1 Reproducibility and provenance contract

Every result-bearing workflow is reconstructible from:

```text
workflow name
dataset identity and raw checksum
preprocessing identity
split and cutoff
client/cohort definition
horizon
representation and detector checkpoint hashes
configuration identity and full configuration_hash
material configuration subset hash for each artifact
seed streams
upstream artifact identities
operator-library identity
solver outcome
producer code fingerprint
relevant numerical/software-environment fingerprint
repository commit
scientific outcome and run result
```

`repository_commit` and the complete `configuration_hash` are whole-run audit fields. Artifact reuse is governed by artifact-specific dependency fingerprints.

Each reusable artifact manifest contains at minimum:

```text
artifact_type
artifact_identity
producer
owner_workflow
dependency_fingerprint
material_configuration_hash
producer_code_fingerprint
relevant_environment_fingerprint
upstream_artifact_identities
scientific_key
content_checksum_or_checkpoint_hash
state = COMPLETE
completion_record_checksum
created_by_repository_commit
```

The dependency fingerprint is a deterministic digest of only material dependencies that can change the artifact's scientific/numerical value. Depending on the boundary, these include:

* raw-data checksum/source identity;
* parser/schema/data-quality rules;
* cutoff/split/client/cohort/eligibility definitions;
* fitted preprocessing identity;
* architecture, loss, optimizer, schedule, and training hyperparameters;
* relevant seed stream;
* exact upstream artifact identities;
* control matching and nuisance-estimation definitions;
* operator-library/toolchain identity;
* calibration grid/objectives/tie rules;
* solver method/material tolerances;
* metric/statistical definitions;
* executed producer code fingerprint;
* numerical/runtime versions on the executed producer path.

The producer code fingerprint is derived from semantics-relevant code for the producer rather than the repository as a whole. Changes to unrelated workflows, tests, documentation, comments, CLI help, logging, or presentation do not invalidate scientific artifacts unless they are material dependencies of that producer.

Required scientific artifacts include:

* raw-data/dataset-preparation manifests;
* chronological cutoff/split manifests;
* client/cohort manifests;
* fitted preprocessing transforms;
* cutoff-fixed representation/base-detector checkpoints;
* reusable encoded/scored observations and transition summaries where materialized;
* client nuisance bases and constraints;
* historical minimum-norm reference points, radii, feasible sets, and centers;
* temporal model/process-error sets;
* nested calibration results;
* operator-library identities, validity records, and action displacements;
* prospective feasible sets and diameter bounds;
* action intervals, states, certificates, and abstentions;
* hardened/baseline checkpoints;
* workflow results and statistical summaries;
* manuscript-facing evidence.

An upstream artifact may be reused only when its state is `COMPLETE`, integrity checks pass, and its dependency fingerprint equals the currently expected fingerprint.

Artifacts are written to staging and atomically committed only after content checks, manifest checks, scientific invariants, and mandatory output checks pass. Interrupted producers leave no reusable artifact; incomplete staging content is cleaned before retry.

## 34.2 Deterministic execution

The implementation uses deterministic execution wherever supported:

* set Python/NumPy/PyTorch random streams only from the designated roadmap seed;
* enable PyTorch deterministic algorithms;
* disable cuDNN benchmark/autotuning choices that can change kernels between runs;
* record Python, NumPy, PyTorch, CUDA/cuDNN, CVXPY, ECOS, LIEF, `pefile`, Android toolchain, UPX, and external baseline/operator tool versions when they are on the producer path;
* use deterministic dataset ordering before any seeded sampling;
* use stable canonical serialization/hashing for identities and tie-breaking.

If a required GPU operation has no deterministic implementation, that producer executes the affected operation on CPU rather than accepting an unspecified numerical tolerance. A deterministic CPU fallback is part of the relevant environment fingerprint.

Solver results remain subject to the explicit numerical tolerances in §20. Numerical tolerance does not authorize scientific threshold changes.

## 34.3 Failure, retry, resume, and selective invalidation

Infrastructure faults such as worker interruption, filesystem failure, cluster preemption, or unrelated process crash may be retried with identical scientific inputs and seed identities.

Normal retry behavior is:

```text
validate existing artifacts
→ reuse compatible COMPLETE artifacts
→ identify missing/stale descendants
→ recompute only the nearest invalid boundary and affected descendants
→ continue execution
```

After a code change, recalculate producer code fingerprints:

* change outside an artifact's producer/dependency path → artifact remains valid;
* proven non-semantic change on the path that leaves the producer fingerprint/material dependency digest unchanged → artifact remains valid;
* material producer/dependency change → artifact and only its descendants become stale;
* siblings and unrelated branches remain valid.

When a parent artifact is regenerated, stale descendants are identified through the reverse dependency index and excluded from active evidence. If the regenerated parent has the same dependency fingerprint and deterministic content identity, compatible descendants remain valid.

Solver divergence, infeasibility, NaN production, conditioning failure, or convergence failure is a numerical/scientific outcome unless independently demonstrated to be infrastructure corruption. It may not be rerun with a different seed, altered tolerance, or relaxed scientific constraint merely to obtain a favorable result.

Permanently unavailable confirmatory outcomes remain in the evidence record under §17.8.

## 34.4 End-to-end reproducibility verification

There is no separate replication experiment, namespace, scientific workflow, threshold-selection phase, or post-analysis protocol.

Reproducibility is verified by the ordinary dependency-aware workflow contract:

1. every manuscript result traces through `evidence_index.json` to complete full-precision outputs and their provenance;
2. every scientific artifact traces recursively to immutable acquired input checksums, configuration, seeds, producer code, environment, and upstream identities;
3. deterministic producers must regenerate the same content identity from the same complete dependency fingerprint;
4. a clean-room verification, when desired, consists only of removing regenerable `outputs/` and `results/` state and executing the same normal CLI sequence from immutable raw inputs and the authoritative configuration;
5. such verification introduces no new scientific workflow, parameter, threshold, comparator, dataset, or statistical decision.

Scientific decisions may not be changed because confirmatory or later-real outcomes are unfavorable. Reproducibility is therefore an invariant of normal execution rather than a separate scientific stage.

# 35. Claim-to-Evidence Synthesis and Manuscript Evidence

## 35.1 Claim-to-evidence map

| Claim                                                                                   | Decisive evidence                                                                   | Support criterion                                                                                                       | Falsification / limitation                                                                                   |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Control-compatible sets are scientifically valid.**                                   | control- and malicious-sample sweeps; control-span-violation sweep; coverage theory | set/action coverage remain calibrated at declared level when assumptions and budgets hold                               | systematic undercoverage falsifies; controls do not causally isolate attacker evolution                      |
| **Action identification can occur without full transition identification.**             | common-intersection experiment; action rotation; functional-identifiability theory  | unresolved full-state subspace coexists with narrow/certified valid-action intervals                                    | absence of such a regime falsifies; no full-state reconstruction claim                                       |
| **A point recommendation can remain scientifically ambiguous.**                         | real action-certificate validation; point-versus-set ablation                       | point-positive ambiguous actions are less prospectively reliable than certified actions                                 | equivalent/superior ambiguous-action reliability falsifies; does not imply every point method is invalid     |
| **Complementary federation provides identification gain beyond replication.**           | matched redundant/complementary synthetic and source-aware real experiments         | complementary geometry contracts action-relevant uncertainty beyond matched redundant sampling                          | effect disappearing under sample matching falsifies; no claim that arbitrary federation is beneficial        |
| **Action-specific identification adds information beyond a global spectral criterion.** | fixed-global-geometry action rotation; global-versus-action-specific ablation       | intervals/certification change with action orientation while global rank/spectrum remain fixed                          | equal predictive ability from global metrics falsifies; global metrics remain useful diagnostics             |
| **FedACT certificates are prospectively informative.**                                  | Real-Data Action-Certificate Validation                                             | certified actions outperform point-positive ambiguous and matched random valid actions under locked statistics          | no prespecified separation falsifies; certificates do not predict arbitrary zero-days                        |
| **Certified-action hardening reduces pre-feedback exposure at acceptable clean cost.**  | Main Prospective FedACT Evaluation                                                  | early FNR/exposure improves materially while clean degradation remains acceptable                                       | no material benefit or unacceptable clean cost falsifies; no universal robustness                            |
| **FedACT fails gracefully through uncertainty or abstention.**                          | failure-boundary evaluation                                                         | adverse geometry/assumption regimes widen intervals, increase ambiguity, or abstain                                     | persistent high confidence under genuine non-identification falsifies; not all violations need be detectable |
| **Temporal ordering contributes prospective information.**                              | temporal shuffle and no-dynamics ablations                                          | correct chronology materially outperforms shuffled/no-change alternatives                                               | equivalent shuffled-history performance falsifies; temporal model itself not novel                           |
| **The mechanism generalizes to a second chronological corpus.**                         | EMBER2024 cross-corpus evaluation                                                   | control → uncertainty → certificate → prospective-consequence chain replicates unchanged in scientific semantics        | mechanism failure limits/falsifies; no arbitrary-domain claim                                                |
| **Action-focused client selection can improve communication efficiency.**               | optional communication-limited client selection                                     | greater weighted width reduction per client than random/sample-count selection and comparison with established selector | no advantage falsifies secondary claim; not a general new experimental-design principle                      |

At evidence completion, every claim receives exactly one state:

```text
SUPPORTED
PARTIALLY_SUPPORTED
FALSIFIED
INSUFFICIENT_EVIDENCE
```

State assignment is deterministic. A non-composite claim uses §17.10 directly: `SUPPORTED`, `FALSIFIED`, or `INSUFFICIENT_EVIDENCE`. `PARTIALLY_SUPPORTED` is permitted only for a claim whose table row explicitly requires more than one distinct evidentiary component: at least one required component must be `SUPPORTED`, no required component may be `FALSIFIED`, and at least one remaining required component must be `INSUFFICIENT_EVIDENCE`. If any required component is `FALSIFIED`, the composite claim is `FALSIFIED`. If none is supported and at least one is insufficient, the composite claim is `INSUFFICIENT_EVIDENCE`.

No claim is removed because its outcome is unfavorable.

## 35.2 Required manuscript evidence

### Main tables

**Dataset and chronology specification**

Contains:

* dataset roles;
* client semantics;
* cutoff schedule;
* cohort definitions;
* control availability;
* action availability.

**Primary prospective outcomes**

Contains:

* early FNR/exposure;
* clean cost;
* action-certification precision;
* primary paired effect estimates and intervals.

**Mechanism ablations**

Contains:

* point versus set;
* global versus action-specific identification;
* generic uncertainty;
* random valid actions;
* temporal shuffle.

**Federation complementarity**

Contains:

* redundant;
* complementary;
* local;
* centralized;
* action-width contraction;
* certification changes.

### Main figures

**Transition unresolved, action resolved**

Synthetic geometry showing a nontrivial feasible transition set with a narrow action support interval.

**Complementary constraint contraction**

Action intervals under local, redundant, and complementary client constraints.

**Real certificate validity**

Later-real alignment distributions for:

* certified actions;
* point-positive ambiguous actions;
* negatively identified actions;
* matched random valid actions.

**Prospective security outcome**

Early-horizon FNR/exposure curves across the main methods.

**Graceful failure surfaces**

Action width, certification, and abstention versus:

* control violation;
* action-nullspace overlap;
* horizon.

### Appendix evidence

Include:

* mathematical proofs;
* analytical solver checks;
* full synthetic grids;
* calibration procedures;
* sensitivity surfaces;
* eigengap diagnostics;
* control reconstruction;
* radius dependence;
* leave-one-client-out stability;
* baseline parity checks;
* failed/infeasible run accounting;
* operator validity audit;
* reproducibility manifests.

### Reporting semantics

All scientific computations and exported metrics/statistics evidence retain full precision. Rounding is presentation-only and uses the configured significant-figure counts. P-values below the configured display threshold are rendered as `< 0.0001`. Undefined values are rendered as `—`, and every undefined metric requires its exclusion count to be reported.

## 35.3 Required limitations

The manuscript must preserve, where applicable:

* synchronized unmeasured nuisance cannot be separated from threat evolution without additional evidence;
* private/local threat evolution can invalidate the shared-transition interpretation;
* poor controls produce wider uncertainty or abstention;
* valid operators may not span identified action directions;
* long horizons can destroy action identifiability;
* synthetic clients do not prove natural federation;
* corrupted clients are stress-tested but not solved generally;
* representation choice can alter nuisance geometry;
* prospective claims require historical predictability;
* the later-real transition proxy contains residual nuisance and pooled private-transition bias because true \(g\) is unobserved.

## 35.4 Completion criterion

FedACT research execution is complete when:

* every mandatory scientific workflow has a terminal scientific outcome and the optional client-selection study is either completed or explicitly omitted as optional;
* required statistical synthesis and sensitivity analyses are complete;
* end-to-end provenance and deterministic reproducibility checks in §34 are complete;
* every manuscript claim maps to evidence and one of the four final claim states;
* null, adverse, infeasible, assumption-violating, abstaining, and falsifying outcomes are retained;
* all required manuscript tables, figures, statistics, and full-precision supporting evidence can be regenerated from authoritative code, configuration, data identities, and provenance.

The final evidence must preserve the complete scientific chain:

$$
\boxed{
\text{distributed control evidence}
\rightarrow
\text{compatible transition uncertainty}
\rightarrow
\text{action-specific uncertainty}
\rightarrow
\text{decision-identifiable certificate}
\rightarrow
\text{valid proactive challenge}
\rightarrow
\text{prospective hardening}
\rightarrow
\text{later-real evidence}
}
$$

A favorable detector score without this chain does **not** establish the FedACT contribution.

---

# PART IV — EXECUTION INFRASTRUCTURE AND CLI CONTRACT

# 36. Repository Structure

```text
fedact/
│
├── README.md                                      # Project overview, scientific scope, setup, and canonical CLI workflow.
├── pyproject.toml                                 # Python package metadata, dependencies, tooling, and fedact console entry point.
├── uv.lock                                        # Locked Python dependency graph for reproducible environments.
├── noxfile.py                                     # Reproducible linting, testing, architecture-check, and validation sessions.
├── Makefile                                       # Short developer commands for setup, checks, tests, and canonical CLI entry points.
├── .gitignore                                     # Excludes generated outputs, caches, environments, and other non-versioned artifacts.
│
├── configs/                                       # Configuration data only; scientific behavior remains defined by the roadmap/code.
│   ├── fedact.yaml                                # Single authoritative production configuration for the locked FedACT study.
│   ├── tests.yml                                  # Test-only configuration for deterministic lightweight fixtures.
│   └── smoke.yml                                  # Smoke-only configuration for fast implementation validation.
│
├── data/
│   └── raw -> /external/datasets                  # SYMLINK — immutable external raw datasets; never written by FedACT.
│
├── outputs/                                       # Git-ignored generated computational workspace; may contain large reusable artifacts.
│   │
│   ├── preprocessing/                             # Dataset preparation and cutoff-safe preprocessing products.
│   │   ├── inventories/                           # Raw discovery, file inventories, checksums, and acquisition identities.
│   │   ├── validation/                            # Chronology, support, control, client-semantics, operator, and representation audits.
│   │   ├── prepared/                              # Canonical parsed LAMDA and EMBER2024 records derived from immutable raw data.
│   │   ├── splits/                                # Cutoff-safe train/validation/test, client, cohort, and eligibility partitions.
│   │   ├── features/                              # Fitted cutoff-safe transforms and materialized transformed feature products.
│   │   └── metadata/                              # Dataset observations, exclusions, cutoff metadata, and preprocessing provenance.
│   │
│   ├── artifacts/                                 # Project-wide artifacts reusable only when dependency fingerprints are compatible.
│   │   ├── models/                                # Shared cutoff-fixed representation and base-detector checkpoints.
│   │   │   ├── representations/
│   │   │   └── detectors/
│   │   │
│   │   ├── scores/                                # Shared heavy encoding/scoring products reused across compatible workflows.
│   │   │   ├── encodings/
│   │   │   ├── detector_scores/
│   │   │   └── detector_predictions/
│   │   │
│   │   ├── fitted/                                # Reusable fitted scientific objects produced before experiment-specific evaluation.
│   │   │   ├── nuisance/
│   │   │   ├── constraints/
│   │   │   ├── calibration/
│   │   │   ├── temporal/
│   │   │   └── feasible_sets/
│   │   │
│   │   ├── baselines/                             # Shared baseline artifacts when their scientific condition is identical across workflows.
│   │   │   ├── checkpoints/
│   │   │   ├── scores/
│   │   │   └── parity/
│   │   │
│   │   ├── derived/                               # Reusable derived FedACT objects that are not themselves fitted models.
│   │   │   ├── transitions/
│   │   │   ├── action_displacements/
│   │   │   ├── operators/
│   │   │   └── certificates/
│   │   │
│   │   └── provenance/                            # Project-wide artifact lifecycle, completion, and dependency metadata.
│   │       ├── manifests/
│   │       ├── completion_records/
│   │       └── indexes/
│   │           ├── artifact_index.jsonl           # Generated active-artifact index containing identities and validity states.
│   │           └── dependency_index.json          # Generated forward/reverse dependency index for selective invalidation.
│   │
│   ├── experiments/                               # Workflow-owned execution state; create one subtree per descriptive scientific workflow.
│   │   └── <descriptive-experiment-name>/         # Placeholder only; one subtree is created for each descriptive scientific workflow.
│   │       ├── artifacts/
│   │       │   ├── fitted/
│   │       │   ├── predictions/
│   │       │   └── derived/
│   │       │
│   │       ├── evaluations/
│   │       │   ├── records/
│   │       │   ├── comparisons/
│   │       │   └── aggregates/
│   │       │
│   │       ├── metrics/
│   │       │   ├── per_seed/
│   │       │   ├── per_condition/
│   │       │   └── aggregate/
│   │       │
│   │       ├── statistics/
│   │       │   ├── tests/
│   │       │   ├── confidence_intervals/
│   │       │   ├── effects/
│   │       │   └── multiplicity/
│   │       │
│   │       ├── checkpoints/
│   │       │   ├── training/
│   │       │   └── execution/
│   │       │
│   │       ├── diagnostics/
│   │       │   ├── scientific/
│   │       │   ├── numerical/
│   │       │   └── runtime/
│   │       │
│   │       ├── logs/
│   │       │   ├── execution/
│   │       │   └── failures/
│   │       │
│   │       └── provenance/
│   │           ├── configuration/
│   │           ├── data/
│   │           ├── seeds/
│   │           ├── code/
│   │           ├── environment/
│   │           └── dependencies/
│   │
│   └── cache/                                     # Disposable or reproducible intermediate material never treated as scientific evidence.
│       ├── preprocessing/
│       ├── models/
│       ├── evaluation/
│       ├── analysis/                              # Bootstrap draws and other heavy statistical intermediates remain here.
│       └── staging/                               # Atomic-write staging area; incomplete content is never reusable.
│
├── results/                                       # Compact verified manuscript-facing evidence; never consumed by scientific execution.
│   │
│   ├── experiments/
│   │   └── <descriptive-experiment-name>/         # Placeholder for verified exports from one completed scientific workflow.
│   │       ├── figures/
│   │       │   ├── main/
│   │       │   └── supplementary/
│   │       │
│   │       ├── tables/
│   │       │   ├── main/
│   │       │   └── supplementary/
│   │       │
│   │       ├── metrics/
│   │       │   ├── primary/
│   │       │   ├── secondary/
│   │       │   └── summary/
│   │       │
│   │       └── statistics/
│   │           ├── tests/
│   │           ├── confidence_intervals/
│   │           ├── effects/
│   │           └── multiplicity/
│   │
│   └── project_summary/                           # Cross-workflow manuscript evidence and compact reproducibility information.
│       ├── figures/
│       │   ├── main/
│       │   └── supplementary/
│       │
│       ├── tables/
│       │   ├── main/
│       │   └── supplementary/
│       │
│       ├── metrics/
│       │   ├── primary/
│       │   └── summary/
│       │
│       ├── statistics/
│       │   ├── comparisons/
│       │   ├── confidence_intervals/
│       │   ├── effects/
│       │   └── multiplicity/
│       │
│       └── reproducibility/
│           ├── configuration/
│           ├── datasets/
│           ├── seeds/
│           ├── software/
│           └── execution/
│               └── evidence_index.json            # Generated compact index linking manuscript evidence to verified output artifact identities.
│
├── docs/
│   └── Roadmap.md                                 # Authoritative FedACT scientific and execution roadmap tracked with the implementation.
│
├── src/
│   └── fedact/
│       │
│       ├── __init__.py                            # FedACT package identity and public package metadata.
│       │
│       ├── domain/                                # Shared strongly typed scientific and execution vocabulary.
│       │   ├── __init__.py                        # Exposes stable domain types without leaking implementation details.
│       │   ├── enums.py                           # Dataset, workflow, action-state, abstention, outcome, failure, and artifact-state enums.
│       │   └── records.py                         # Typed scientific identities and records shared across package boundaries.
│       │
│       ├── config/                                # Loading and validation of the locked configuration data.
│       │   ├── __init__.py                        # Exposes configuration loading and validated configuration types.
│       │   ├── models.py                          # Typed models for fedact.yaml, tests.yml, and smoke.yml configuration data.
│       │   ├── loading.py                         # Loads configuration, computes configuration hashes, and resolves test/smoke overlays.
│       │   └── validation.py                      # Enforces configuration schema, locked ranges, cross-field constraints, and YAML discipline.
│       │
│       ├── datasets/                              # Canonical data preparation, chronology, splitting, and corpus-specific semantics.
│       │   ├── __init__.py                        # Exposes supported dataset identities and common dataset contracts.
│       │   ├── records.py                         # Canonical sample, cutoff, split, client, cohort, and eligibility records.
│       │   ├── chronology.py                      # Rolling cutoffs, historical windows, transition windows, and leakage-safe temporal boundaries.
│       │   ├── splits.py                          # Cutoff-safe train/validation/test construction and support eligibility logic.
│       │   ├── audits.py                          # Shared chronology, support, control, client-semantics, operator, and representation audit orchestration.
│       │   │
│       │   ├── synthetic/
│       │   │   ├── __init__.py                    # Exposes the known-truth synthetic dataset generator.
│       │   │   ├── generator.py                   # Generates locked FedACT observation-model components and known ground truth.
│       │   │   ├── geometry.py                    # Constructs redundant/complementary nuisance spaces, nullspaces, and controlled action geometry.
│       │   │   └── validation.py                  # Validates orthogonality, intersections, deterministic replay, and generator invariants.
│       │   │
│       │   ├── lamda/
│       │   │   ├── __init__.py                    # Exposes LAMDA acquisition/preparation semantics to the common dataset layer.
│       │   │   ├── loader.py                      # Discovers and parses the pinned LAMDA release and authoritative source fields.
│       │   │   ├── preprocessing.py               # Applies LAMDA variance filtering and cutoff-fitted standardization.
│       │   │   ├── semantics.py                   # Defines LAMDA labels, chronology, family cohorts, temporal clients, and benign control matching.
│       │   │   └── validation.py                  # Validates LAMDA schema, timestamps, labels, feature basis, support, and observed metadata.
│       │   │
│       │   └── ember2024/
│       │       ├── __init__.py                    # Exposes EMBER2024 acquisition/preparation semantics to the common dataset layer.
│       │       ├── loader.py                      # Discovers and parses the pinned EMBER2024 Win32/Win64 study subset.
│       │       ├── preprocessing.py               # Applies count-feature log1p transforms and cutoff-fitted standardization.
│       │       ├── semantics.py                   # Defines EMBER2024 chronology, family cohorts, Win32/Win64 clients, and control strata.
│       │       └── validation.py                  # Validates EMBER2024 schema, formats, timestamps, tags, support, and observed metadata.
│       │
│       ├── models/                                # Locked FedACT representation and detector architectures.
│       │   ├── __init__.py                        # Exposes the representation encoder and detector model constructors.
│       │   ├── representation.py                  # Implements the fixed 512→256→64 tabular MLP representation architecture.
│       │   └── detector.py                        # Implements the fixed linear sigmoid detector over cutoff-fixed 64-dimensional embeddings.
│       │
│       ├── training/                              # Training procedures distinct from FedACT transition identification.
│       │   ├── __init__.py                        # Exposes cutoff-safe model fitting and hardening entry points.
│       │   ├── representation.py                  # Trains and selects cutoff-safe representation checkpoints using locked validation semantics.
│       │   ├── detector.py                        # Trains the base detector against the exact cutoff-fixed representation checkpoint.
│       │   ├── federated.py                       # Implements ordinary federated detector training used only where the roadmap requires it.
│       │   └── hardening.py                       # Performs FedACT certified-action hardening and completes hardened checkpoints before later-real evaluation.
│       │
│       ├── scoring/                               # Cutoff-fixed inference products reusable across compatible scientific workflows.
│       │   ├── __init__.py                        # Exposes deterministic encoding and detector-scoring operations.
│       │   ├── encoding.py                        # Materializes cutoff-fixed representation embeddings for cutoff-safe sample populations.
│       │   ├── detector.py                        # Computes detector scores and predictions from immutable checkpoints and sample identities.
│       │   └── validation.py                      # Checks score completeness, checkpoint/sample identity, determinism, and leakage invariants.
│       │
│       ├── operators/                             # Domain-valid problem-space actions and their validity contracts.
│       │   ├── __init__.py                        # Exposes the dataset-specific operator libraries.
│       │   ├── common.py                          # Shared operator records, composition limits, displacement construction, and zero-displacement rejection.
│       │   ├── lamda.py                           # Implements the locked APK benign-gadget and permission-neutral resource operators.
│       │   ├── ember2024.py                       # Implements the locked PE mutation families using LIEF/pefile-compatible transformations.
│       │   └── validation.py                      # Enforces format, executability, maliciousness, behavioral-equivalence, coverage, and provenance rules.
│       │
│       ├── fedact/                                # Scientific core of Federated Action-Certified Threat Dynamics.
│       │   ├── __init__.py                        # Exposes FedACT scientific primitives without exposing experiment orchestration.
│       │   ├── transitions.py                     # Computes cutoff-safe malicious transition summaries from cutoff-fixed representations.
│       │   ├── controls.py                        # Builds matched benign control transitions and held-out control-quality diagnostics.
│       │   ├── nuisance.py                        # Estimates nuisance covariance, rank, eigengaps, low-rank bases, and projection operations.
│       │   ├── uncertainty.py                     # Computes sampling, subspace, control-span, private-transition, and plausibility uncertainty components.
│       │   ├── constraints.py                     # Builds, validates, and transmits client constraint summaries and quality-gate outcomes.
│       │   ├── feasible_sets.py                   # Constructs historical compatible sets, plausibility intersections, centers, and infeasibility diagnostics.
│       │   ├── solver.py                          # Solves CVXPY/ECOS support and feasibility problems under the locked numerical contract.
│       │   ├── temporal.py                        # Fits stable low-capacity temporal dynamics and propagates prospective feasible sets.
│       │   ├── actions.py                         # Computes normalized operator displacements, action support intervals, and action-conditioning quantities.
│       │   ├── certification.py                   # Applies positive/negative/ambiguous states, certificates, stability gates, challenge selection, and abstention.
│       │   └── client_selection.py                # Implements the optional equal-budget action-interval-contraction client-selection objective.
│       │
│       ├── calibration/                           # Nested pre-cutoff scientific calibration only.
│       │   ├── __init__.py                        # Exposes nested calibration results and validated selection operations.
│       │   ├── nested.py                          # Creates inner pseudo-futures and evaluates only cutoff-safe calibration candidates.
│       │   ├── selection.py                       # Applies the locked calibration objective hierarchy and deterministic tie-breaking rules.
│       │   └── validation.py                      # Validates calibration provenance, temporal isolation, candidate completeness, and failure semantics.
│       │
│       ├── baselines/                             # Required comparator implementations and parity validation.
│       │   ├── __init__.py                        # Exposes only roadmap-approved baseline families and parity checks.
│       │   ├── identification.py                  # Implements subtraction, projection, point reconstruction, covariance-weighted, and generic uncertainty comparators.
│       │   ├── security.py                        # Implements static, temporal, generative, random-mutation, hardening, and reactive security comparators.
│       │   ├── federation.py                      # Implements centralized, local-only, ordinary-federated, redundant, and complementary comparator conditions.
│       │   └── parity.py                          # Verifies chronology, information budget, capacity, tuning, action-count, and implementation parity before use.
│       │
│       ├── experiments/                           # Roadmap-defined scientific workflow ownership and manipulations.
│       │   ├── __init__.py                        # Exposes descriptive workflow definitions used by the CLI/runtime.
│       │   ├── definitions.py                     # Defines locked workflow scopes, owned outputs, required datasets, and optionality.
│       │   ├── dependencies.py                    # Encodes the fixed scientific workflow dependency order and shared producer requirements.
│       │   ├── math_verification.py               # Implements exact-set, identifiability, support-bound, monotonicity, solver, degeneracy, and infeasibility verification.
│       │   ├── synthetic_geometry.py              # Implements the full locked known-truth geometry, uncertainty, sample-size, conditioning, and failure sweeps.
│       │   ├── action_certificate_validation.py   # Implements later-real comparison of certified, ambiguous, negative, and matched-random valid actions.
│       │   ├── prospective_evaluation.py          # Implements the locked rolling-cutoff FedACT hardening and prospective baseline evaluation.
│       │   ├── ablations.py                       # Implements all novelty-critical control, set, uncertainty, temporal, action, width-gate, and hardening ablations.
│       │   ├── federation.py                      # Implements local/federated, redundant/complementary, centralized-equivalence, and geometry-control experiments.
│       │   ├── failure_boundaries.py              # Implements sparse-control, eigengap, contamination, synchronized-nuisance, geometry, horizon, and corruption boundaries.
│       │   ├── cross_corpus.py                    # Applies unchanged FedACT scientific semantics to the locked EMBER2024 generalization study.
│       │   ├── client_selection.py                # Implements the optional communication-limited equal-budget client-selection study.
│       │   ├── statistical_synthesis.py           # Executes the locked confirmatory contrast and sensitivity workflow over verified experiment evidence.
│       │
│       ├── evaluation/                            # Full-precision scientific outcome construction before statistical synthesis.
│       │   ├── __init__.py                        # Exposes evaluation records, metrics, and validation functions.
│       │   ├── records.py                         # Typed per-dataset/cutoff/cohort/client/action/horizon/seed evaluation records and missingness classifications.
│       │   ├── metrics.py                         # Implements all locked coverage, certification, predictive, geometry, clean-cost, and communication metrics.
│       │   ├── later_real.py                      # Constructs the cutoff-safe later-real transition proxy and prospective action-alignment outcomes.
│       │   ├── exposure.py                        # Computes early-horizon FNR, cumulative pre-adaptation exposure, and time-to-catch-up.
│       │   └── validation.py                      # Rejects invalid denominators, incomplete populations, leakage, mismatched pairing, and malformed metric outputs.
│       │
│       ├── analysis/                              # Statistical inference, sensitivity, and claim-state construction over verified evaluations.
│       │   ├── __init__.py                        # Exposes locked statistical analysis and claim-evaluation operations.
│       │   ├── statistics.py                      # Implements cutoff-clustered BCa bootstrap, Wilcoxon tests, rank-biserial effects, quantiles, and BH correction.
│       │   ├── comparisons.py                     # Builds prespecified paired confirmatory contrasts while preserving cutoff-level dependence.
│       │   ├── sensitivity.py                     # Computes the locked rho, xi, radius, threshold, horizon, rank, coverage, and geometry sensitivity surfaces.
│       │   └── claims.py                          # Maps verified statistical/material-effect evidence to supported, falsified, partial, or insufficient states.
│       │
│       ├── artifacts/                             # Computational artifact identity, storage, provenance, reuse, and invalidation infrastructure.
│       │   ├── __init__.py                        # Exposes artifact lifecycle and path-resolution services to producers and runtime code.
│       │   ├── paths.py                           # Resolves the generic outputs/results directory contract without project-specific top-level sprawl.
│       │   ├── identity.py                        # Computes artifact identities, material-configuration hashes, code fingerprints, and dependency fingerprints.
│       │   ├── manifests.py                       # Reads/writes artifact manifests, completion records, scientific keys, and integrity metadata.
│       │   ├── dependencies.py                    # Maintains forward/reverse dependency indexes and computes selective descendant invalidation.
│       │   ├── lifecycle.py                       # Implements staging, atomic completion, stale marking, incomplete cleanup, and scoped overwrite semantics.
│       │   ├── storage.py                         # Stores and validates large artifacts, checkpoints, arrays, tabular records, and checksum-protected payloads.
│       │   ├── provenance.py                      # Captures raw/config/seed/code/environment/upstream identities required for scientific reconstruction.
│       │   └── validation.py                      # Enforces COMPLETE-only reuse, integrity, fingerprint compatibility, and results/input separation.
│       │
│       ├── runtime/                               # Dependency-aware deterministic execution and recovery services.
│       │   ├── __init__.py                        # Exposes planning, execution, state, and environment services.
│       │   ├── determinism.py                     # Applies seed streams and deterministic/repeatability rules without conflating conceptual randomness.
│       │   ├── environment.py                     # Captures relevant Python, framework, CUDA, solver, and numerical dependency fingerprints.
│       │   ├── logging.py                         # Emits readable diagnostic logs and structured execution events without becoming evidence.
│       │   ├── planning.py                        # Resolves workflows into reusable producers, dependencies, expected work, and nearest valid resume boundaries.
│       │   ├── state.py                           # Tracks workflow/artifact states, scientific outcomes, failures, blocking dependencies, and progress.
│       │   └── executor.py                        # Executes reuse→invalidate→recompute semantics, scoped overwrite, retries, and atomic workflow completion.
│       │
│       ├── reporting/                             # Pure export layer from verified outputs into compact manuscript-facing results.
│       │   ├── __init__.py                        # Exposes verified reporting/export operations only.
│       │   ├── tables.py                          # Renders locked main/supplementary scientific tables from verified full-precision analysis artifacts.
│       │   ├── figures.py                         # Renders locked main/supplementary figures without altering scientific calculations.
│       │   ├── export.py                          # Writes compact verified metrics/statistics/reproducibility evidence into results/ without recomputation.
│       │   └── evidence.py                        # Maintains manuscript claim/evidence traceability and the compact project evidence index.
│       │
│       ├── app.py                                 # Composition root wiring configuration, artifact infrastructure, runtime, scientific workflows, and reporting.
│       │
│       └── cli/
│           ├── __init__.py                        # Exposes the FedACT command-line application.
│           ├── main.py                            # Defines the Typer CLI and registers only roadmap-authorized public commands.
│           └── commands/
│               ├── __init__.py                    # Collects public command handlers without compatibility aliases.
│               ├── doctor.py                      # Implements read-only readiness, validity, stale-artifact, blocker, and next-action inspection.
│               ├── preprocess.py                  # Runs dataset preparation, cutoff/split construction, preprocessing, and real-data audits.
│               ├── plan.py                        # Displays the dependency-resolved scientific plan, reuse scope, recomputation, and blocked work.
│               ├── smoke.py                       # Runs the synthetic generator smoke-validation workflow and scoped overwrite behavior.
│               ├── run.py                         # Executes one predefined scientific workflow with dependency-aware resume and reuse.
│               ├── status.py                      # Reports workflow progress, artifact validity, failures, stale causes, and resume location.
│               └── report.py                      # Exports verified manuscript evidence without retraining, rescoring, recalibration, or reanalysis.
│
└── tests/
    ├── conftest.py
    │
    ├── architecture/
    │   ├── test_structure.py
    │   ├── test_dependencies.py
    │   ├── test_framework_confinement.py
    │   ├── test_code_contracts.py
    │   └── test_config_contracts.py
    │
    ├── unit/
    │   ├── domain/
    │   │   ├── test_enums.py
    │   │   └── test_records.py
    │   │
    │   ├── config/
    │   │   ├── test_models.py
    │   │   ├── test_loading.py
    │   │   └── test_validation.py
    │   │
    │   ├── datasets/
    │   │   ├── test_chronology.py
    │   │   ├── test_splits.py
    │   │   ├── test_audits.py
    │   │   ├── test_synthetic.py
    │   │   ├── test_lamda.py
    │   │   └── test_ember2024.py
    │   │
    │   ├── models/
    │   │   ├── test_representation.py
    │   │   └── test_detector.py
    │   │
    │   ├── training/
    │   │   ├── test_representation_training.py
    │   │   ├── test_detector_training.py
    │   │   ├── test_federated_training.py
    │   │   └── test_hardening.py
    │   │
    │   ├── scoring/
    │   │   ├── test_encoding.py
    │   │   ├── test_detector_scoring.py
    │   │   └── test_validation.py
    │   │
    │   ├── operators/
    │   │   ├── test_common.py
    │   │   ├── test_lamda.py
    │   │   ├── test_ember2024.py
    │   │   └── test_validation.py
    │   │
    │   ├── fedact/
    │   │   ├── test_transitions.py
    │   │   ├── test_controls.py
    │   │   ├── test_nuisance.py
    │   │   ├── test_uncertainty.py
    │   │   ├── test_constraints.py
    │   │   ├── test_feasible_sets.py
    │   │   ├── test_solver.py
    │   │   ├── test_temporal.py
    │   │   ├── test_actions.py
    │   │   ├── test_certification.py
    │   │   └── test_client_selection.py
    │   │
    │   ├── calibration/
    │   │   ├── test_nested.py
    │   │   ├── test_selection.py
    │   │   └── test_validation.py
    │   │
    │   ├── baselines/
    │   │   ├── test_identification.py
    │   │   ├── test_security.py
    │   │   ├── test_federation.py
    │   │   └── test_parity.py
    │   │
    │   ├── experiments/
    │   │   ├── test_definitions.py
    │   │   ├── test_dependencies.py
    │   │   ├── test_math_verification.py
    │   │   ├── test_synthetic_geometry.py
    │   │   ├── test_action_certificate_validation.py
    │   │   ├── test_prospective_evaluation.py
    │   │   ├── test_ablations.py
    │   │   ├── test_federation.py
    │   │   ├── test_failure_boundaries.py
    │   │   ├── test_cross_corpus.py
    │   │   ├── test_client_selection.py
    │   │   ├── test_statistical_synthesis.py
    │   │
    │   ├── evaluation/
    │   │   ├── test_records.py
    │   │   ├── test_metrics.py
    │   │   ├── test_later_real.py
    │   │   ├── test_exposure.py
    │   │   └── test_validation.py
    │   │
    │   ├── analysis/
    │   │   ├── test_statistics.py
    │   │   ├── test_comparisons.py
    │   │   ├── test_sensitivity.py
    │   │   └── test_claims.py
    │   │
    │   ├── artifacts/
    │   │   ├── test_paths.py
    │   │   ├── test_identity.py
    │   │   ├── test_manifests.py
    │   │   ├── test_dependencies.py
    │   │   ├── test_lifecycle.py
    │   │   ├── test_storage.py
    │   │   ├── test_provenance.py
    │   │   └── test_validation.py
    │   │
    │   ├── runtime/
    │   │   ├── test_determinism.py
    │   │   ├── test_environment.py
    │   │   ├── test_planning.py
    │   │   ├── test_state.py
    │   │   └── test_executor.py
    │   │
    │   ├── reporting/
    │   │   ├── test_tables.py
    │   │   ├── test_figures.py
    │   │   ├── test_export.py
    │   │   └── test_evidence.py
    │   │
    │   └── cli/
    │       ├── test_doctor.py
    │       ├── test_preprocess.py
    │       ├── test_plan.py
    │       ├── test_smoke.py
    │       ├── test_run.py
    │       ├── test_status.py
    │       └── test_report.py
    │
    ├── scientific/
    │   ├── test_chronological_information_boundary.py
    │   ├── test_control_quality_contracts.py
    │   ├── test_feasible_set_contracts.py
    │   ├── test_functional_identifiability_contracts.py
    │   ├── test_action_certificate_contracts.py
    │   ├── test_abstention_and_failure_semantics.py
    │   ├── test_statistical_inference_contracts.py
    │   ├── test_baseline_fairness.py
    │   └── test_claim_boundaries.py
    │
    ├── integration/
    │   ├── datasets/
    │   │   ├── test_lamda_pipeline.py
    │   │   ├── test_ember2024_pipeline.py
    │   │   └── test_synthetic_pipeline.py
    │   │
    │   ├── training/
    │   │   ├── test_representation_detector_pipeline.py
    │   │   └── test_federated_training_pipeline.py
    │   │
    │   ├── fedact/
    │   │   ├── test_controls_to_constraints.py
    │   │   ├── test_constraints_to_certificates.py
    │   │   └── test_certificates_to_hardening.py
    │   │
    │   ├── execution/
    │   │   ├── test_dependency_resolution.py
    │   │   ├── test_resume_and_invalidation.py
    │   │
    │   ├── artifacts/
    │   │   ├── test_artifact_lifecycle.py
    │   │   └── test_provenance_round_trip.py
    │   │
    │   └── reporting/
    │       ├── test_verified_export.py
    │       └── test_results_never_feed_execution.py
    │
    ├── e2e/
    │   ├── test_doctor_preprocess_plan.py
    │   ├── test_smoke_and_math_verification.py
    │   ├── test_run_status_report.py
    │   ├── test_reuse_and_recovery.py
    │
    └── smoke/
        └── test_smoke.py
```

`configs/` is version-controlled. `configs/fedact.yaml` is the single authoritative production scientific configuration whose complete contents are reproduced in the Configuration YAML section of this roadmap. `configs/tests.yml` and `configs/smoke.yml` are execution-only configurations for deterministic tests and smoke validation; they do not redefine production scientific parameters or workflow semantics.

The resolved authoritative production configuration produces the `configuration_hash` used for whole-run provenance and configuration-lock verification. Artifact compatibility uses the material configuration subset captured by the dependency fingerprint in §34 and §40, so a change to an unrelated configuration item does not invalidate unaffected artifacts.

`data/raw` is the immutable symlink to `/external/datasets`; FedACT never writes to raw source data.

`tests/` verifies implementation correctness. It does not replace mathematical/numerical scientific verification or synthetic smoke validation.

`outputs/` is Git-ignored regenerable computational working state. Shared reusable artifacts live under `outputs/artifacts/`; workflow-owned execution state lives under `outputs/experiments/<descriptive-experiment-name>/`; disposable intermediates live under `outputs/cache/`.

`results/` contains compact verified manuscript-facing evidence only and is never consumed by scientific execution. Workflow exports live under `results/experiments/<descriptive-experiment-name>/`, while cross-workflow evidence and reproducibility information live under `results/project_summary/`.

`docs/Roadmap.md` is the authoritative roadmap tracked with the implementation.

---

# 37. Runnable Scientific Workflows

The operator selects descriptive scientific workflows rather than internal experiment identifiers.

The CLI does not expose scientific knobs. Datasets, seeds, methods, baselines, ablations, thresholds, horizons, calibration rules, and statistics come from the authoritative configuration and workflow definition.

| CLI workflow | What it executes | Required/automatic dependencies | Principal reusable inputs | Principal owned outputs | Optional |
| --- | --- | --- | --- | --- | --- |
| `math-verification` | §20 mathematical identities, support/center/diameter solver checks, degeneracy, infeasibility, synchronized-nuisance verification | configuration authority | solver/config fixtures | verification metrics, solver diagnostics, completion manifest | No |
| `synthetic-geometry` | §22 full synthetic theory/geometry program | mathematical verification and synthetic smoke validation | verified solver, generator/config | synthetic sweep source data, metrics, diagnostics | No |
| `action-certificate-validation` | §26 real-data mechanism validation | real-data feasibility/control audit, baseline parity, nested calibration | prepared splits, immutable checkpoints, scores/summaries, constraints, calibrated sets/actions | action-group outcomes, future-alignment metrics, certificate precision | No |
| `prospective-evaluation` | §27 prospective hardening evaluation | action-certificate validation and required fitted artifacts | compatible checkpoints/scores/calibration/certificates, baseline parity artifacts | hardened checkpoints, comparator outcomes, exposure/predictive metrics | No |
| `ablations` | §28 novelty-critical ablations | prospective evaluation and matching upstream artifacts | compatible prepared/trained/scored artifacts; only manipulated boundary varies | ablation outcomes | No |
| `federation` | §29 federation/complementarity experiments | prospective evaluation and compatible client/control artifacts | same cutoff/checkpoints/scores plus local/redundant/complementary constraint variants | federation contrasts/diagnostics | No |
| `failure-boundaries` | §30 robustness/failure-boundary experiments | prospective evaluation and synthetic/real prerequisites as applicable | compatible base artifacts plus declared stress manipulations | boundary curves and diagnostics | No |
| `cross-corpus` | §31 secondary-corpus generalization | primary mechanism, robustness, EMBER2024 preprocessing/calibration | EMBER2024 prepared/trained/scored/calibrated artifacts | cross-corpus mechanism/outcome evidence | No |
| `client-selection` | §32 communication-limited client selection | federation | compatible federation constraints/actions | budget-matched selection outcomes | **Yes** |
| `statistical-synthesis` | §33 confirmatory synthesis and sensitivity | all mandatory confirmatory workflows | verified full-precision outcomes | paired contrasts, intervals, tests, multiplicity, sensitivity summaries | No |

`fedact smoke` runs §21 directly and is a prerequisite of `synthetic-geometry`.

Real-data feasibility/control auditing is owned by `fedact preprocess`. Baseline parity and nested calibration are produced once per compatible dependency fingerprint and reused automatically.

## 37.1 Scientific dependency order

```text
math-verification
  → smoke
    → synthetic-geometry
      → real-data feasibility/control audit
        → baseline parity
          → nested calibration
            → action-certificate-validation
              → prospective-evaluation
                → ablations
                → federation
                  → failure-boundaries
                    → cross-corpus
                      → client-selection (optional)
                        → statistical-synthesis
```

The optional client-selection workflow does not block statistical synthesis when intentionally omitted.

Scientific dependency order does not imply unconditional recomputation. A downstream workflow may reuse any complete compatible artifact from an earlier successful workflow, even after another workflow failed later in the sequence.

## 37.2 Shared fitted-artifact ownership

| Shared producer boundary | Invoked when | Owned artifacts | Reuse scope |
| --- | --- | --- | --- |
| Representation/detector fit | a real-data workflow or representation audit first requires a missing/stale retraining-cadence checkpoint | cutoff-fixed representation and base-detector checkpoints plus training manifest | every compatible monthly cutoff/workflow under §9.5 |
| Encoding/scoring and transition-summary materialization | a downstream workflow first requires scores, encodings, transitions, nuisance inputs, or action displacements | encoded/scored observations, transition/control summaries, reusable action displacements | workflows with the same checkpoint, samples/splits, controls/operators, and producer fingerprint |
| Baseline fit/parity | a required comparator is first needed | baseline checkpoints, parity manifests, reusable baseline scores where scientifically identical | every compatible downstream comparison |
| Nested pre-cutoff calibration | a dataset/cutoff first requires calibrated values | selected calibration result and calibrated set/model parameters | every compatible downstream workflow at that dataset/cutoff |

These producers have one logical owner per artifact identity even when more than one public command can trigger them. `preprocess` remains the owner of dataset preparation, splits, cutoff/client/cohort manifests, fitted feature preprocessing, and real-data feasibility inputs. Representation/detector checkpoints are not duplicated inside scientific workflows, and scoring is not repeated when the checkpoint/sample identity is unchanged.

# 38. Automatic Dependency Resolution

When

```bash
fedact run <experiment>
```

is invoked, the implementation follows this exact recovery/reuse model:

```text
validate existing artifacts
→ reuse compatible artifacts
→ identify stale descendants
→ recompute only what is necessary
→ continue execution
```

It:

1. resolves the predefined scientific workflow into internal producers and required upstream artifacts;
2. computes the expected dependency fingerprint for each required boundary;
3. validates indexed candidates for `COMPLETE` state, integrity, expected fingerprint, and scientific invariants;
4. reuses every compatible artifact, irrespective of which compatible workflow first produced it;
5. marks incompatible artifacts stale and traverses the reverse dependency index to mark only their descendants stale;
6. cleans incomplete/staging artifacts and removes stale descendants from the active index before regeneration;
7. executes only missing or stale producers from the nearest invalid boundary;
8. executes the requested experiment over its prescribed datasets, cutoffs, cohorts, methods, variants, and seeds;
9. computes only missing/stale metrics and statistical products whose dependencies changed;
10. atomically commits complete artifacts and updates dependency indexes;
11. stores the workflow's scientific outcome.

A valid unfavorable result is a completed scientific workflow. Infrastructure/runtime failure is an execution failure. Leakage, incompatible configuration, invalid provenance, or violated scientific invariants make the affected artifact/result invalid rather than silently usable.

A failure in one branch does not automatically mark sibling branches or already-valid parents stale.

# 39. Run Identity, Idempotency, Resume, and Overwrite

## 39.1 Run and artifact identity

The operator-facing run is identified by the selected scientific workflow and its locked execution scope. Internally, compatibility is artifact-specific.

Each artifact identity is deterministic over the material inputs that determine it, including as applicable:

* dataset/raw identity;
* cutoff and split;
* client/cohort set;
* horizon;
* seed stream used by the artifact producer;
* material configuration subset;
* exact upstream artifact identities;
* representation/checkpoint identity;
* operator/control/calibration/metric definitions;
* semantics-relevant producer code fingerprint;
* relevant numerical environment fingerprint.

The full repository commit and full configuration hash are recorded for provenance but do not force broad invalidation when unrelated material is changed.

The operator interacts with descriptive workflow names rather than opaque run IDs.

## 39.2 Execution state

The execution layer may use:

```text
NOT_STARTED
BLOCKED
RUNNING
COMPLETED
FAILED
INVALID
```

Artifact state is stricter and uses:

```text
STAGING
COMPLETE
STALE
INVALID
```

Only `COMPLETE` artifacts are reusable.

The scientific outcome inside a completed result remains distinct and uses §19.2 and §17.7 semantics.

A workflow is `COMPLETED` only when:

* every required internal run has valid provenance;
* locked seeds and configurations are represented;
* mandatory outputs exist;
* metrics validate;
* any scientific non-success outcome has its required diagnostic evidence.

## 39.3 Default resume and idempotency

Resume is the default behavior; no separate `--resume` flag is required.

Repeating the same command:

* validates its existing artifacts;
* reuses compatible upstream and workflow-owned artifacts;
* cleans incomplete outputs;
* recomputes only missing or stale artifacts;
* does not create duplicate active results.

If `prospective-evaluation` fails after its compatible preprocessing, checkpoints, scores, calibration, and action-certificate artifacts have completed, rerunning the same command resumes from the first missing/stale prospective artifact. It does not retrain or rescore merely because the previous prospective run crashed.

## 39.4 `--overwrite`

`--overwrite` means **force regeneration of the artifacts owned by the explicitly selected command scope**, not “delete and recompute every upstream dependency.” Valid upstream dependencies are still reused.

```bash
fedact run <experiment> --overwrite
```

forces regeneration of that workflow's owned result artifacts and any workflow-private intermediates while preserving compatible shared parents. Their downstream descendants are invalidated only if the regenerated artifact identity/content changes in a way material to those descendants.

```bash
fedact preprocess <dataset> --overwrite
```

forces regeneration of the selected dataset-preparation/preprocessing/split artifacts for that dataset. If regenerated deterministic identities remain identical, compatible descendants remain reusable. If a material identity changes, only affected descendants become stale.

```bash
fedact smoke --overwrite
```

reruns smoke-owned correctness artifacts only.

```bash
fedact report <experiment> --overwrite
```

rerenders manuscript-facing outputs from existing verified scientific/analysis artifacts and never retrains, rescores, recalibrates, or reruns statistical decisions.

Overwrite does not change:

* seeds;
* thresholds;
* methods;
* datasets;
* calibration rules;
* scientific configuration.

Prior replaced results remain excluded from active confirmatory analysis; required historical failure/audit records remain retained according to provenance rules.

---

# 40. Reuse, Selective Invalidation, and Artifact Cleanup

## 40.1 Reuse rule

An artifact is reusable only when:

```text
state == COMPLETE
AND integrity checks pass
AND dependency_fingerprint == expected_dependency_fingerprint
AND all referenced upstream artifacts are COMPLETE and active
```

Cache location, filesystem path, creation time, or repository commit equality is insufficient to establish validity.

Whether an artifact came from reuse/cache or fresh computation must never change the scientific result.

Cache manipulation is not part of the public scientific CLI.

## 40.2 Selective invalidation boundaries

| Artifact boundary | Changes that invalidate this boundary | Changes that do not invalidate this boundary by themselves |
| --- | --- | --- |
| Dataset preparation | raw checksum/source changes; parser/schema semantics; row inclusion/exclusion, malformed/duplicate/missing handling; chronology-field extraction semantics | downstream model/statistics/report code; comments/docs/tests; unrelated dataset code |
| Preprocessing and splits | prepared-data identity; cutoff/split/client/cohort/eligibility definitions; feature selection/transforms; normalization fitting rules; split seed if used | model architecture changes; later calibration/statistical/report changes |
| Training/checkpoints | preprocessed training/validation split identity; architecture; optimizer/loss/schedule/early stopping; training seed; training producer code; relevant framework/numerical changes | evaluation metrics; report formatting; unrelated ablation code; later statistical-test code |
| Scoring and transition summaries | checkpoint identity; scored sample/split identity; encoding/scoring/transition/control-summary code; action-displacement definition where applicable | calibration thresholds alone; statistical/report changes |
| Calibration / feasible sets / certificates | relevant scores/summaries/constraints; inner pseudo-cutoffs; calibration grid/objective/tie-break; uncertainty/plausibility/temporal-set definitions; solver material settings; `tau_align`/`tau_amb`; calibration seed where applicable | downstream detector metric/report formatting changes |
| Evaluation | evaluated checkpoint/certificate/baseline identity; test/later-real split identity; comparator/evaluation procedure; metric definitions; evaluation seed where applicable | bootstrap/multiplicity/report-only changes |
| Statistical analysis | full-precision evaluation inputs; pairing/unit-of-inference; estimator/test/bootstrap/multiplicity/sensitivity definitions; analysis seed | figure layout, labels, rounding, prose |
| Figures/tables/reporting | analysis/evidence identity; table/figure specification; rounding/presentation code | changes to unrelated scientific producers; report regeneration never invalidates scientific artifacts |

A material change invalidates the artifact at the first affected boundary and only its descendants. It does not invalidate ancestors or siblings.

Examples:

* changing a figure title rerenders the figure only;
* changing a bootstrap procedure invalidates statistical summaries and reports, not training or evaluation metrics;
* fixing action-interval solver semantics invalidates feasible sets/action intervals and their descendants, not dataset preparation, preprocessing, checkpoints, or cutoff-fixed scores;
* fixing detector scoring semantics invalidates scores and descendants, not the trained checkpoint if training code/input is unchanged;
* changing model architecture invalidates training and all descendants but preserves prepared data and compatible splits;
* changing the LAMDA parser invalidates LAMDA preparation and descendants but does not invalidate EMBER2024 artifacts;
* editing README files, tests, comments, logging, CLI help, or an unrelated workflow does not invalidate scientific artifacts;
* a new repository commit alone does not invalidate anything.

## 40.3 Stale-descendant cleanup

Every complete artifact registers forward dependencies and reverse consumers.

When an artifact becomes stale:

1. it is removed from the active-compatible index;
2. only descendants that reference that artifact identity are marked stale;
3. stale result/report descendants are excluded immediately from analysis/report selection;
4. incomplete staging outputs are deleted before retry;
5. stale physical files may be deleted automatically once no active artifact references them and required audit metadata has been retained;
6. unaffected artifacts remain active and reusable.

No stale descendant may silently remain active after a parent changes.

## 40.4 Shared expensive-artifact policy

The following expensive artifacts are computed once per compatible dependency fingerprint and reused across all scientifically compatible experiments:

* parsed/prepared corpora;
* cutoff-safe splits and preprocessing transforms;
* retraining-cadence cutoff-fixed representations and base-detector checkpoints;
* baseline checkpoints where the baseline fit is identical;
* encoded samples and detector scores;
* malicious/control transition summaries;
* nuisance bases and client constraints;
* action displacements for the same cutoff-fixed representation/operator/source sample;
* clean/reference comparator outputs whose scientific condition is identical;
* nested calibration results for the same dataset/cutoff and upstream identities;
* historical/prospective feasible sets and action intervals when their complete dependency fingerprint matches;
* full-precision evaluation metrics consumed by multiple analyses;
* statistical source objects consumed by multiple tables/figures.

A workflow may intentionally require a scientifically altered variant of one of these artifacts; that variant receives a distinct dependency fingerprint and does not overwrite the shared reference artifact.

---

# 41. Logging

Execution provides:

* readable execution logs;
* structured status/provenance sufficient to diagnose failures and reconstruct what ran.

Logs are diagnostic only.

Manuscript values come from verified reproducible result artifacts, never console output or log text.

---

# 42. Command-Line Interface

```bash
fedact doctor

fedact preprocess
fedact preprocess <dataset>
fedact preprocess --overwrite
fedact preprocess <dataset> --overwrite

fedact plan

fedact smoke
fedact smoke --overwrite

fedact run <experiment>
fedact run <experiment> --overwrite

fedact status
fedact status <experiment>

fedact report
fedact report <experiment>
fedact report <experiment> --overwrite
```

Defined real-data selectors:

```text
lamda
ember2024
```

Defined scientific workflows:

```text
math-verification
synthetic-geometry
action-certificate-validation
prospective-evaluation
ablations
federation
failure-boundaries
cross-corpus
client-selection
statistical-synthesis
```

No compatibility aliases exist for removed numbered or machine-style names.

The CLI selects predefined scientific work. It does not expose arbitrary flags for seeds, thresholds, horizons, methods, baseline sets, ablation definitions, calibration values, or statistical tests.

Default command behavior is dependency-aware resume and reuse. `--overwrite` has the scoped semantics in §39.4; it is not a global cache purge.

## 42.0 CLI-to-artifact map

| Command | Reads / validates | Writes / owns | Reuse and resume semantics |
| --- | --- | --- | --- |
| `fedact doctor` | raw/config identities, artifact/dependency index, workflow manifests | no scientific artifacts | read-only validity and next-action inspection |
| `fedact preprocess [dataset]` | raw corpus, dataset/config definitions, existing preparation artifacts | prepared data, cutoffs/splits, client/cohort manifests, fitted preprocessing, feasibility/audit artifacts; may trigger the representation fit needed by the representation audit | validates/reuses compatible boundaries independently |
| `fedact plan` | configuration, workflow graph, active artifact/dependency index | no scientific artifacts | read-only reuse/recompute plan |
| `fedact smoke` | generator/config/solver fixtures and existing smoke artifacts | smoke correctness manifest/results | reuses complete compatible smoke output |
| `fedact run <experiment>` | required compatible upstream artifacts | selected-workflow outputs plus missing shared dependencies it is authorized to trigger | default resume; reuses valid parents/intermediates; computes only missing/stale descendants |
| `fedact status [experiment]` | workflow/artifact/dependency manifests | no scientific artifacts | read-only progress/resume-point inspection |
| `fedact report [experiment]` | verified active analysis/scientific artifacts | manuscript-facing figures/tables/metrics/statistics and reproducibility evidence | reporting-only regeneration; never triggers scientific recomputation |

## 42.1 `doctor`

Read-only.

Reports:

* raw-data availability/checksum validity;
* preprocessing readiness;
* client/cohort readiness;
* operator-library readiness;
* configuration validity and `configuration_hash` consistency;
* workflow state/progress;
* reusable artifact counts by boundary;
* incomplete/staging artifacts;
* stale artifacts and invalidating dependency;
* failed/invalid internal runs;
* blocking dependency;
* nearest resumable boundary;
* exact recomputation scope;
* next valid scientific action.

## 42.2 `preprocess`

```bash
fedact preprocess
fedact preprocess lamda
fedact preprocess ember2024
fedact preprocess --overwrite
fedact preprocess lamda --overwrite
```

Without an argument, preprocess every real dataset requiring missing or stale preparation artifacts. With a selector, process only that corpus.

It owns and validates:

```text
raw discovery/checksum
→ canonical parsed preparation
→ chronology/cutoff construction
→ split/client/cohort construction
→ fitted cutoff-safe preprocessing transforms
→ real-data feasibility/control audits
```

It performs raw discovery, checksum validation, parsing, deterministic duplicate/malformed/missing handling, cutoff-safe preprocessing, split/cohort/client construction, exclusion recording, and the chronology/support/control/client/operator/representation audits in §23.

`--overwrite` regenerates only the selected dataset's preprocess-owned artifacts and applies §40 selective invalidation.

## 42.3 `plan`

Read-only.

Displays workflow order, dependencies, dataset requirements, predefined methods/baselines/ablations, seed families, expected internal run counts, artifact producers/consumers, reusable artifacts, stale/missing boundaries, exact recomputation versus reuse, blocked work, and currently executable work.

The plan is generated from the authoritative configuration/workflow definitions and active dependency index.

## 42.4 `smoke`

Runs §21 Synthetic Generator Smoke Validation. It accepts no dataset, seed, or scientific-parameter flags. A valid existing result is reused by default; failed/interrupted smoke output is cleaned and rerun only at the missing/stale boundary.

Smoke supports implementation correctness only.

## 42.5 `run`

```bash
fedact run math-verification
fedact run synthetic-geometry
fedact run action-certificate-validation
fedact run prospective-evaluation
fedact run prospective-evaluation --overwrite
```

Executes the predefined lifecycle of the selected scientific workflow, including dependency resolution, compatible reuse, incomplete-output cleanup, stale-descendant detection, nearest-valid-boundary resume, required metrics/statistics, scientific-invariant validation, and provenance checks.

It must not retrain, rescore, recalibrate, or reevaluate a compatible expensive parent merely because another workflow first produced it.

A correctly executed null, adverse, infeasible, expected-abstention, or insufficient-evidence result is still a completed workflow. Technical failure or invalid execution returns failure while preserving previously complete compatible artifacts.

## 42.6 `status`

Without an argument, shows concise state/progress for all workflows. With a workflow name, shows expected/completed internal runs, reused/new artifacts, failed/invalid runs, incomplete cleanup, stale artifacts and causes, blocking dependencies, nearest valid resume point, last scientific outcome, and active output location.

## 42.7 `report`

```bash
fedact report
fedact report prospective-evaluation
fedact report prospective-evaluation --overwrite
```

Materializes manuscript-facing evidence from completed verified scientific/analysis artifacts.

It does not retrain models, regenerate scores, recalibrate parameters, rerun evaluation, or alter statistical decisions.

Without an argument, it exports all eligible completed workflows under `results/experiments/` and refreshes `results/project_summary/reproducibility/execution/evidence_index.json`.

Reporting has its own dependency fingerprints. Presentation-only changes rerender only affected figures/tables/evidence packages.

## 42.8 Typical execution

```bash
fedact doctor
fedact preprocess
fedact smoke
fedact plan

fedact run math-verification
fedact run synthetic-geometry
fedact run action-certificate-validation
fedact run prospective-evaluation
fedact run ablations
fedact run federation
fedact run failure-boundaries
fedact run cross-corpus
# optional: fedact run client-selection
fedact run statistical-synthesis

fedact report
```

Because `run` resolves missing dependencies and reuses compatible artifacts, this sequence documents scientific order rather than requiring manual orchestration or repeated upstream computation.

# 43. `outputs/` and `results/`

## 43.1 `outputs/` — regenerable computational workspace

The paths below are the rendered directory layout defined by the repository structure and the `artifacts` configuration block. They are not independent path definitions.

```text
outputs/
├── preprocessing/
│   ├── inventories/
│   ├── validation/
│   ├── prepared/
│   ├── splits/
│   ├── features/
│   └── metadata/
│
├── artifacts/
│   ├── models/
│   │   ├── representations/
│   │   └── detectors/
│   ├── scores/
│   │   ├── encodings/
│   │   ├── detector_scores/
│   │   └── detector_predictions/
│   ├── fitted/
│   │   ├── nuisance/
│   │   ├── constraints/
│   │   ├── calibration/
│   │   ├── temporal/
│   │   └── feasible_sets/
│   ├── baselines/
│   │   ├── checkpoints/
│   │   ├── scores/
│   │   └── parity/
│   ├── derived/
│   │   ├── transitions/
│   │   ├── action_displacements/
│   │   ├── operators/
│   │   └── certificates/
│   └── provenance/
│       ├── manifests/
│       ├── completion_records/
│       └── indexes/
│           ├── artifact_index.jsonl
│           └── dependency_index.json
│
├── experiments/
│   └── <descriptive-experiment-name>/
│       ├── artifacts/
│       │   ├── fitted/
│       │   ├── predictions/
│       │   └── derived/
│       ├── evaluations/
│       │   ├── records/
│       │   ├── comparisons/
│       │   └── aggregates/
│       ├── metrics/
│       │   ├── per_seed/
│       │   ├── per_condition/
│       │   └── aggregate/
│       ├── statistics/
│       │   ├── tests/
│       │   ├── confidence_intervals/
│       │   ├── effects/
│       │   └── multiplicity/
│       ├── checkpoints/
│       │   ├── training/
│       │   └── execution/
│       ├── diagnostics/
│       │   ├── scientific/
│       │   ├── numerical/
│       │   └── runtime/
│       ├── logs/
│       │   ├── execution/
│       │   └── failures/
│       └── provenance/
│           ├── configuration/
│           ├── data/
│           ├── seeds/
│           ├── code/
│           ├── environment/
│           └── dependencies/
│
└── cache/
    ├── preprocessing/
    ├── models/
    ├── evaluation/
    ├── analysis/
    └── staging/
```

`outputs/` is working state and is regenerable from:

* code;
* locked configuration;
* acquired data identities;
* seeds.

Project-wide reusable artifacts are stored under `outputs/artifacts/` only when their dependency fingerprints are compatible across consuming workflows. Workflow-specific execution artifacts, evaluations, metrics, statistics, checkpoints, diagnostics, logs, and provenance are stored under `outputs/experiments/<descriptive-experiment-name>/`.

Every reusable payload under `outputs/` is referenced by an artifact manifest and completion record under the applicable provenance boundary, with the project-wide active and dependency indexes stored at:

```text
outputs/artifacts/provenance/indexes/artifact_index.jsonl
outputs/artifacts/provenance/indexes/dependency_index.json
```

Directory existence alone never establishes validity.

`outputs/cache/staging/` is disposable. A crash may leave files there, but no downstream workflow may consume them. The next relevant command cleans abandoned staging content before recomputation.

Stale payloads are excluded from the active artifact index immediately. They may be physically deleted once no active artifact references them and their required audit record is retained.

Storage layout is not itself scientific evidence.

## 43.2 `results/` — manuscript-facing evidence

`fedact report` exports only completed, verified active evidence. `results/` is never consumed as a scientific execution input.

```text
results/
├── experiments/
│   └── <descriptive-experiment-name>/
│       ├── figures/
│       │   ├── main/
│       │   └── supplementary/
│       ├── tables/
│       │   ├── main/
│       │   └── supplementary/
│       ├── metrics/
│       │   ├── primary/
│       │   ├── secondary/
│       │   └── summary/
│       └── statistics/
│           ├── tests/
│           ├── confidence_intervals/
│           ├── effects/
│           └── multiplicity/
│
└── project_summary/
    ├── figures/
    │   ├── main/
    │   └── supplementary/
    ├── tables/
    │   ├── main/
    │   └── supplementary/
    ├── metrics/
    │   ├── primary/
    │   └── summary/
    ├── statistics/
    │   ├── comparisons/
    │   ├── confidence_intervals/
    │   ├── effects/
    │   └── multiplicity/
    └── reproducibility/
        ├── configuration/
        ├── datasets/
        ├── seeds/
        ├── software/
        └── execution/
            └── evidence_index.json
```

No:

* cache;
* diagnostic log;
* failed result;
* invalid result;
* stale artifact;
* incomplete analysis;

may enter `results/`.

Every exported result references the exact complete scientific/analysis artifact identities from which it was rendered. If any referenced parent becomes stale, the result is removed from `results/project_summary/reproducibility/execution/evidence_index.json` and must be regenerated after the affected scientific descendants are recomputed.

Every manuscript number must trace through the evidence index to the full-precision verified scientific records and provenance retained under `outputs/` and to the compact reproducibility evidence under `results/project_summary/reproducibility/`.

Reporting applies only the numerical presentation values in the `reporting` block; the fixed reporting semantics are defined in §35.2.
