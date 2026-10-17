import { motion, type Variants } from 'framer-motion';
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Database,
  FlaskConical,
  Github,
  Layers,
  Lightbulb,
  Lock,
  Network,
  ScrollText,
  Shield,
  Sigma,
  Sparkles,
  Zap,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const GITHUB_URL = 'https://github.com/delphi-platform/delphi';

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.05 * i, duration: 0.45, ease: 'easeOut' },
  }),
};

/* ------------------------------------------------------------------ */
/* Content                                                             */
/* ------------------------------------------------------------------ */

const CAPABILITIES = [
  {
    icon: Database,
    title: 'Dataset intelligence',
    description:
      'Versioned ingestion with automated quality scoring, column profiling, outlier and missing-data analysis, and analytical readiness checks.',
  },
  {
    icon: Sigma,
    title: 'Statistical engine',
    description:
      'Hypothesis tests, effect sizes, correlations, and assumption checks — selected automatically from your data and business goal.',
  },
  {
    icon: Network,
    title: 'Causal inference',
    description:
      'Interactive DAGs, backdoor adjustment, treatment-effect estimation, and refutation tests. Correlation is where Delphi starts, not where it stops.',
  },
  {
    icon: FlaskConical,
    title: 'Counterfactual simulation',
    description:
      'Monte Carlo intervention modelling with uncertainty quantification, ROI projection, and risk scoring — before you commit resources.',
  },
  {
    icon: Lightbulb,
    title: 'Decision intelligence',
    description:
      'Ranked, defensible recommendations with explicit tradeoffs, constraints, and confidence — decision science, not gut feel.',
  },
  {
    icon: Bot,
    title: 'AI Decision Copilot',
    description:
      'A business analyst that explains verified results in plain language. Every claim cites stored evidence. It never invents a number.',
  },
] as const;

const PIPELINE = [
  { icon: Database, label: 'Data', detail: 'Versioned datasets, quality scoring' },
  { icon: Sigma, label: 'Statistics', detail: 'Tests, effects, distributions' },
  { icon: Network, label: 'Causality', detail: 'DAGs, treatment effects' },
  { icon: FlaskConical, label: 'Simulation', detail: 'What-if, ROI, risk' },
  { icon: Lightbulb, label: 'Decision', detail: 'Ranked recommendations' },
  { icon: ScrollText, label: 'Executive', detail: 'Board-ready narratives' },
] as const;

const ENTERPRISE = [
  {
    icon: Layers,
    title: 'Clean Architecture monolith',
    description:
      'Strict inward-only dependency rule across presentation, application, domain, and infrastructure. Modules extract cleanly if scale demands it.',
  },
  {
    icon: Shield,
    title: 'Multi-tenant security',
    description:
      'Organization-scoped RBAC, JWT with refresh rotation, audit trail, rate limiting, security headers, and a published threat model.',
  },
  {
    icon: Zap,
    title: 'Production infrastructure',
    description:
      'Redis-backed job queue and cache, background workers, circuit breakers, structured tracing, and an operations dashboard.',
  },
  {
    icon: Lock,
    title: 'Trustworthy AI, by design',
    description:
      'The copilot consumes only verified engine outputs through a validated context layer. Responses are rejected if citations cannot be verified.',
  },
] as const;

const FAQ = [
  {
    q: 'Is Delphi another LLM analytics wrapper?',
    a: 'No. Every number comes from statistical, causal, simulation, and decision engines built on NumPy, SciPy, Statsmodels, and Polars. The LLM layer only explains stored results — responses that cite non-existent analyses are rejected before they reach you.',
  },
  {
    q: 'How is this different from a BI dashboard?',
    a: 'Dashboards describe what happened. Delphi estimates why it happened (causal inference), what happens if you intervene (counterfactual simulation), and what you should do (decision science) — with assumptions and uncertainty stated explicitly.',
  },
  {
    q: 'Can I run it locally?',
    a: 'Yes. One docker compose command starts the full stack: React frontend, FastAPI backend, PostgreSQL, and Redis. Sample case-study datasets are included so you can explore the entire workflow immediately.',
  },
  {
    q: 'What about my data?',
    a: 'Delphi is self-hosted and open source (MIT). Data never leaves your infrastructure. The AI copilot defaults to a deterministic offline provider; external LLMs are strictly opt-in.',
  },
  {
    q: 'Is it production-ready?',
    a: 'The platform ships with multi-tenant RBAC, audit logging, background job infrastructure, circuit breakers, health probes, 100+ automated tests, and CI quality gates for both backend and frontend.',
  },
] as const;

/* ------------------------------------------------------------------ */
/* Sub-components                                                      */
/* ------------------------------------------------------------------ */

function SectionHeading({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-80px' }}
      custom={0}
      variants={fadeUp}
      className="mx-auto mb-12 max-w-2xl text-center"
    >
      <p className="text-primary mb-2 text-[11px] font-semibold tracking-[0.16em] uppercase">
        {eyebrow}
      </p>
      <h2 className="text-display text-3xl text-balance sm:text-4xl">{title}</h2>
      {subtitle ? (
        <p className="text-muted-foreground mt-3 text-base text-balance">{subtitle}</p>
      ) : null}
    </motion.div>
  );
}

/** Stylized product frame — a believable analytics view without shipping screenshots. */
function HeroMock() {
  const bars = [42, 68, 55, 80, 62, 91, 74];
  return (
    <div className="border-border/80 bg-card mx-auto w-full max-w-4xl rounded-xl border shadow-2xl shadow-black/8">
      <div className="border-border/80 flex items-center gap-1.5 border-b px-4 py-3">
        <span className="bg-border size-2.5 rounded-full" />
        <span className="bg-border size-2.5 rounded-full" />
        <span className="bg-border size-2.5 rounded-full" />
        <span className="text-muted-foreground ml-3 font-mono text-[11px]">
          delphi — decision workspace
        </span>
      </div>
      <div className="grid gap-4 p-4 sm:grid-cols-[1fr_240px]">
        <div className="space-y-4">
          <div className="border-border/80 rounded-lg border p-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-medium">Treatment effect — delivery time → churn</span>
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                significant
              </span>
            </div>
            <div className="flex h-28 items-end gap-2">
              {bars.map((h, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex-1 rounded-t-[3px]',
                    i === 5 ? 'bg-primary' : 'bg-muted-foreground/20',
                  )}
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>
            <p className="text-muted-foreground mt-3 font-mono text-[11px]">
              ATE −4.2 pp per day saved · 95% CI [−5.1, −3.3]
            </p>
          </div>
          <div className="border-border/80 rounded-lg border p-4">
            <p className="text-sm font-medium">Recommendation #1 — Invest in fulfilment speed</p>
            <p className="text-muted-foreground mt-1 font-mono text-[11px]">
              ROI 3.4× · risk 0.18 · confidence 0.87 · evidence: Causal #12, Sim #8
            </p>
          </div>
        </div>
        <div className="border-border/80 hidden flex-col gap-3 rounded-lg border p-4 sm:flex">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Sparkles className="text-primary size-4" />
            AI Copilot
          </div>
          <div className="bg-muted rounded-lg p-3 text-xs leading-relaxed">
            Reducing delivery time is the highest-leverage intervention. The effect is causal, not
            correlational — see{' '}
            <span className="text-primary font-medium">[Causal Analysis #12]</span>.
          </div>
          <div className="text-muted-foreground mt-auto text-[10px]">
            Every statement cites verified evidence
          </div>
        </div>
      </div>
    </div>
  );
}

function PipelineSection() {
  return (
    <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
      {PIPELINE.map((step, i) => {
        const Icon = step.icon;
        return (
          <motion.div
            key={step.label}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
            custom={i}
            variants={fadeUp}
            className="relative"
          >
            <Card className="h-full">
              <CardContent className="flex flex-col items-center gap-2 p-4 text-center">
                <div className="bg-primary/10 text-primary flex size-9 items-center justify-center rounded-md">
                  <Icon className="size-4" />
                </div>
                <p className="text-sm font-semibold">{step.label}</p>
                <p className="text-muted-foreground text-xs">{step.detail}</p>
              </CardContent>
            </Card>
            {i < PIPELINE.length - 1 ? (
              <ArrowRight className="text-muted-foreground/40 absolute top-1/2 -right-4 hidden size-4 -translate-y-1/2 lg:block" />
            ) : null}
          </motion.div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

export function LandingPage() {
  return (
    <div className="w-full overflow-x-clip">
      {/* Hero — plotting paper, editorial serif, one vermilion signal. */}
      <section className="relative">
        <div aria-hidden className="bg-plot-grid absolute inset-x-0 top-0 -z-10 h-[620px]" />
        <div
          aria-hidden
          className="from-background/10 via-background/60 to-background absolute inset-x-0 top-0 -z-10 h-[620px] bg-gradient-to-b"
        />
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center px-6 pt-24 pb-20 text-center">
          <motion.div
            initial="hidden"
            animate="visible"
            custom={0}
            variants={fadeUp}
            className="border-border/80 bg-card text-muted-foreground mb-6 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium shadow-xs"
          >
            <span className="bg-primary size-1.5 rounded-full" />
            Version 1.0 — open source & production-ready
          </motion.div>

          <motion.h1
            initial="hidden"
            animate="visible"
            custom={1}
            variants={fadeUp}
            className="text-display max-w-3xl text-5xl text-balance sm:text-6xl"
          >
            The analytics platform that answers <em className="text-primary">why</em>
          </motion.h1>

          <motion.p
            initial="hidden"
            animate="visible"
            custom={2}
            variants={fadeUp}
            className="text-muted-foreground mt-6 max-w-2xl text-lg text-balance"
          >
            Dashboards describe. Delphi explains, simulates, and recommends — with statistics,
            causal inference, and decision science. AI narrates the evidence; it never invents it.
          </motion.p>

          <motion.div
            initial="hidden"
            animate="visible"
            custom={3}
            variants={fadeUp}
            className="mt-8 mb-16 flex flex-wrap items-center justify-center gap-3"
          >
            <Button asChild size="lg">
              <Link to="/register">
                Start analyzing free
                <ArrowRight className="size-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a href={GITHUB_URL} target="_blank" rel="noreferrer">
                <Github className="size-4" />
                Star on GitHub
              </a>
            </Button>
          </motion.div>

          <motion.div
            initial="hidden"
            animate="visible"
            custom={4}
            variants={fadeUp}
            className="w-full"
          >
            <HeroMock />
          </motion.div>
        </div>
      </section>

      {/* Why Delphi */}
      <section className="border-border/70 border-y">
        <div className="mx-auto grid w-full max-w-6xl gap-px px-6 py-14 text-center sm:grid-cols-3">
          {[
            ['What happened?', 'Traditional BI', 'text-muted-foreground'],
            ['What will happen?', 'Machine learning', 'text-muted-foreground'],
            ['Why — and what should we do?', 'Delphi', 'text-primary'],
          ].map(([q, who, cls]) => (
            <div key={q} className="px-4 py-2">
              <p className={cn('text-display text-lg', cls)}>{q}</p>
              <p className="text-muted-foreground mt-1 text-sm">{who}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Capabilities */}
      <section className="mx-auto w-full max-w-6xl px-6 py-24">
        <SectionHeading
          eyebrow="Capabilities"
          title="A complete decision pipeline, not a chart library"
          subtitle="Six engines that turn raw data into defensible action — each transparent, each auditable."
        />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map((capability, index) => {
            const Icon = capability.icon;
            return (
              <motion.div
                key={capability.title}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-80px' }}
                custom={index}
                variants={fadeUp}
              >
                <Card className="hover:border-primary/25 h-full transition-colors duration-200">
                  <CardContent className="flex flex-col gap-3">
                    <div className="bg-primary/10 text-primary flex size-9 items-center justify-center rounded-md">
                      <Icon className="size-4" />
                    </div>
                    <CardTitle className="text-base">{capability.title}</CardTitle>
                    <CardDescription>{capability.description}</CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Workflow / architecture */}
      <section className="bg-muted/40 border-border/70 border-y">
        <div className="mx-auto w-full max-w-6xl px-6 py-24">
          <SectionHeading
            eyebrow="How it works"
            title="From dataset to decision in one auditable flow"
            subtitle="Each stage consumes the verified output of the last. Nothing is a black box."
          />
          <PipelineSection />
          <motion.p
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={2}
            variants={fadeUp}
            className="text-muted-foreground mx-auto mt-10 max-w-2xl text-center text-sm"
          >
            Built as a Clean Architecture modular monolith: FastAPI + SQLAlchemy backend, React 19
            frontend, PostgreSQL and Redis. One service to deploy, layered to evolve.
          </motion.p>
        </div>
      </section>

      {/* AI trust section */}
      <section className="mx-auto w-full max-w-6xl px-6 py-24">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            custom={0}
            variants={fadeUp}
          >
            <p className="text-primary mb-2 text-[11px] font-semibold tracking-[0.16em] uppercase">
              Trustworthy AI
            </p>
            <h2 className="text-display text-3xl text-balance sm:text-4xl">
              An AI analyst that cannot hallucinate a number
            </h2>
            <p className="text-muted-foreground mt-4 text-base">
              The AI Decision Copilot works from a structured context of verified engine outputs. A
              validation layer rejects any response that cites analyses that don&apos;t exist or
              introduces figures that were never computed.
            </p>
            <ul className="mt-6 space-y-3">
              {[
                'Engines compute — the AI only explains',
                'Every claim carries an evidence citation',
                'Responses failing validation are rejected, not shown',
                'Provider-agnostic: OpenAI, Azure, or fully offline',
              ].map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="text-primary mt-0.5 size-4 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </motion.div>
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            custom={1}
            variants={fadeUp}
          >
            <Card>
              <CardContent className="space-y-3 p-5">
                <div className="bg-muted ml-auto w-fit max-w-[85%] rounded-lg px-3 py-2 text-sm">
                  Why does Delphi recommend reducing delivery time?
                </div>
                <div className="border-border/80 max-w-[92%] rounded-lg border px-3 py-2 text-sm leading-relaxed">
                  The recommendation is grounded in the full pipeline:{' '}
                  <span className="text-primary font-medium">[Statistical Analysis #1]</span>{' '}
                  establishes the difference is reliable,{' '}
                  <span className="text-primary font-medium">[Causal Analysis #1]</span> estimates
                  the intervention effect, and{' '}
                  <span className="text-primary font-medium">[Simulation #1]</span> stress-tests it
                  under uncertainty.
                  <div className="mt-2 flex flex-wrap gap-1">
                    {['Statistical Analysis #1', 'Causal Analysis #1', 'Simulation #1'].map((c) => (
                      <span
                        key={c}
                        className="bg-primary/10 text-primary rounded-full px-2 py-0.5 text-[10px] font-medium"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Enterprise */}
      <section className="bg-muted/40 border-border/70 border-y">
        <div className="mx-auto w-full max-w-6xl px-6 py-24">
          <SectionHeading
            eyebrow="Enterprise-grade"
            title="Built like a product, engineered like infrastructure"
          />
          <div className="grid gap-4 md:grid-cols-2">
            {ENTERPRISE.map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={item.title}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, margin: '-80px' }}
                  custom={index}
                  variants={fadeUp}
                >
                  <Card className="h-full">
                    <CardContent className="flex gap-4">
                      <div className="bg-primary/10 text-primary flex size-9 shrink-0 items-center justify-center rounded-md">
                        <Icon className="size-4" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{item.title}</CardTitle>
                        <CardDescription className="mt-1.5">{item.description}</CardDescription>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={2}
            variants={fadeUp}
            className="text-muted-foreground mt-10 grid gap-6 text-center sm:grid-cols-4"
          >
            {[
              ['13', 'delivery phases'],
              ['100+', 'automated tests'],
              ['6', 'analytical engines'],
              ['MIT', 'licensed & open'],
            ].map(([value, label]) => (
              <div key={label}>
                <p className="text-display text-foreground text-4xl tabular-nums">{value}</p>
                <p className="mt-1 text-xs tracking-wide uppercase">{label}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Open source */}
      <section className="mx-auto w-full max-w-6xl px-6 py-24">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            custom={0}
            variants={fadeUp}
          >
            <p className="text-primary mb-2 text-[11px] font-semibold tracking-[0.16em] uppercase">
              Open source
            </p>
            <h2 className="text-display text-3xl text-balance sm:text-4xl">
              Read the code behind every conclusion
            </h2>
            <p className="text-muted-foreground mt-4 text-base">
              Analytical trust requires transparency. Delphi is MIT-licensed with documented
              architecture decisions, a published threat model, and realistic case-study datasets so
              you can verify the entire pipeline yourself.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild variant="outline">
                <a href={GITHUB_URL} target="_blank" rel="noreferrer">
                  <Github className="size-4" />
                  View repository
                </a>
              </Button>
              <Button asChild variant="ghost">
                <a href={`${GITHUB_URL}/tree/main/docs`} target="_blank" rel="noreferrer">
                  <ScrollText className="size-4" />
                  Documentation
                </a>
              </Button>
            </div>
          </motion.div>
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            custom={1}
            variants={fadeUp}
            className="border-border/80 bg-card rounded-xl border p-5 font-mono text-xs leading-relaxed shadow-xs"
          >
            <p className="text-muted-foreground"># Run the full platform locally</p>
            <p className="mt-2">
              <span className="text-primary">$</span> git clone {GITHUB_URL.replace('https://', '')}
            </p>
            <p>
              <span className="text-primary">$</span> cp .env.example .env
            </p>
            <p>
              <span className="text-primary">$</span> docker compose up --build
            </p>
            <p className="text-muted-foreground mt-3"># Frontend → localhost:3000</p>
            <p className="text-muted-foreground"># API docs → localhost:8000/docs</p>
          </motion.div>
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-muted/40 border-border/70 border-y">
        <div className="mx-auto w-full max-w-3xl px-6 py-24">
          <SectionHeading eyebrow="FAQ" title="Questions, answered honestly" />
          <div className="space-y-3">
            {FAQ.map((item, index) => (
              <motion.details
                key={item.q}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-60px' }}
                custom={index}
                variants={fadeUp}
                className="border-border/80 bg-card group rounded-lg border px-5 py-4"
              >
                <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium">
                  {item.q}
                  <ArrowRight className="text-muted-foreground size-4 transition-transform duration-200 group-open:rotate-90" />
                </summary>
                <p className="text-muted-foreground mt-3 text-sm leading-relaxed">{item.a}</p>
              </motion.details>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative">
        <div aria-hidden className="bg-plot-grid absolute inset-0 -z-10" />
        <div
          aria-hidden
          className="from-background via-background/60 to-background absolute inset-0 -z-10 bg-gradient-to-b"
        />
        <div className="mx-auto w-full max-w-6xl px-6 py-24 text-center">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={0}
            variants={fadeUp}
          >
            <h2 className="text-display mx-auto max-w-2xl text-3xl text-balance sm:text-5xl">
              Stop reporting what happened.
              <br />
              <em className="text-primary">Start deciding what to do.</em>
            </h2>
            <p className="text-muted-foreground mx-auto mt-5 max-w-xl text-base">
              Upload a dataset and walk the full pipeline — statistics to causal effects to
              simulations to a recommendation you can defend.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Button asChild size="lg">
                <Link to="/register">
                  Get started
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <a href={GITHUB_URL} target="_blank" rel="noreferrer">
                  <Github className="size-4" />
                  GitHub
                </a>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
