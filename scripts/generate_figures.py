#!/usr/bin/env python3
"""Generate figures for the Maslow Machines paper from exported simulation data."""

import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS = os.path.join(BASE, "data", "exports", "stats")
INTERVIEWS = os.path.join(BASE, "data", "interviews")
OUT = os.path.join(BASE, "paper", "figures")
os.makedirs(OUT, exist_ok=True)

# Style
plt.rcParams.update({
    'figure.facecolor': '#0f172a',
    'axes.facecolor': '#1e293b',
    'axes.edgecolor': '#334155',
    'axes.labelcolor': '#e2e8f0',
    'text.color': '#e2e8f0',
    'xtick.color': '#94a3b8',
    'ytick.color': '#94a3b8',
    'grid.color': '#334155',
    'grid.alpha': 0.5,
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'figure.dpi': 200,
})

CYAN = '#22d3ee'
AMBER = '#fbbf24'
EMERALD = '#34d399'
ROSE = '#fb7185'
VIOLET = '#a78bfa'
SKY = '#38bdf8'
ORANGE = '#fb923c'
LIME = '#a3e635'
PINK = '#f472b6'
TEAL = '#2dd4bf'
INDIGO = '#818cf8'
RED = '#f87171'
COLORS = [CYAN, AMBER, EMERALD, ROSE, VIOLET, SKY, ORANGE, LIME, PINK, TEAL, INDIGO, RED]


def load(name):
    with open(os.path.join(STATS, name)) as f:
        return json.load(f)


def era_spans(ax):
    """Add era background shading."""
    ax.axvspan(0, 50, alpha=0.08, color=ROSE, zorder=0)
    ax.axvspan(50, 60, alpha=0.08, color=AMBER, zorder=0)
    ax.axvspan(60, 70, alpha=0.08, color=EMERALD, zorder=0)
    ax.axvline(50, color='#475569', ls='--', lw=0.8, alpha=0.7)
    ax.axvline(60, color='#475569', ls='--', lw=0.8, alpha=0.7)


def era_labels(ax, y_pos):
    """Add era labels at top."""
    ax.text(25, y_pos, 'Era 1: Survival Trap', ha='center', fontsize=8, color='#94a3b8', style='italic')
    ax.text(55, y_pos, 'Era 2', ha='center', fontsize=8, color='#94a3b8', style='italic')
    ax.text(65, y_pos, 'Era 3', ha='center', fontsize=8, color='#94a3b8', style='italic')


# ──────────────────────────────────────────────────────────────
# Figure 1: Control vs Treatment comparison table
# ──────────────────────────────────────────────────────────────
def fig1_comparison():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')

    headers = ['Metric', 'Control\n(No Maslow Drives)', 'Treatment\n(Maslow Drives)']
    data = [
        ['Innovations discovered', '0', '12'],
        ['Structures built', '0', '60'],
        ['Collective rules adopted', '0', '1'],
        ['Specialisation tiers reached', 'None', 'Master (level 4)'],
        ['Mean wellbeing (final)', '0.50 (baseline)', '0.998'],
        ['Mean Maslow level (final)', '1.0 (survival only)', '8.0 (purpose)'],
        ['Messages exchanged', '0', '1,604'],
        ['Social bonds formed', '0', 'Network-wide'],
        ['Civilisation?', 'No', 'Yes'],
    ]

    table = ax.table(cellText=data, colLabels=headers, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.6)

    # Style header
    for j in range(3):
        cell = table[0, j]
        cell.set_facecolor('#334155')
        cell.set_text_props(weight='bold', color='#e2e8f0')
        cell.set_edgecolor('#475569')

    # Style data rows
    for i in range(1, len(data) + 1):
        for j in range(3):
            cell = table[i, j]
            cell.set_facecolor('#1e293b')
            cell.set_edgecolor('#334155')
            cell.set_text_props(color='#e2e8f0')
        # Highlight treatment column
        table[i, 2].set_text_props(color=EMERALD, weight='bold')
        # Dim control column
        table[i, 1].set_text_props(color='#64748b')

    # Last row emphasis
    table[len(data), 1].set_text_props(color=ROSE, weight='bold')
    table[len(data), 2].set_text_props(color=EMERALD, weight='bold')

    ax.set_title('Figure 1: Control vs Treatment — Maslow Drives as Independent Variable', pad=20, fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig1_comparison.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 1: Control vs Treatment comparison")


# ──────────────────────────────────────────────────────────────
# Figure 2: Timeline of parameter changes
# ──────────────────────────────────────────────────────────────
def fig2_timeline():
    fig, ax = plt.subplots(figsize=(12, 4))

    events = [
        (0, 'Simulation starts\n12 agents, 15×15 grid\nHaiku model', CYAN),
        (10, 'First innovation\n(Communication Beacon)', AMBER),
        (20, 'Innovation cluster\n(4 innovations, ticks 19-21)', AMBER),
        (33, 'Second burst begins\n(Recovery Workshop)', VIOLET),
        (46, "Master's Archive\n(11th innovation)", VIOLET),
        (50, 'UPGRADE\nSonnet model + Maslow\ndrives activated', ROSE),
        (52, 'Synthesis Nexus\n(12th & final innovation)', AMBER),
        (55, 'First collective rule\nadopted', EMERALD),
        (60, 'All agents reach\nMaslow level 8', EMERALD),
        (70, 'Simulation ends\nSustained flourishing', SKY),
    ]

    era_spans(ax)
    ax.set_xlim(-2, 72)
    ax.set_ylim(-1, 3)
    ax.axhline(1, color='#475569', lw=2, zorder=1)

    for i, (tick, label, color) in enumerate(events):
        y_offset = 1.6 if i % 2 == 0 else 0.1
        ax.plot(tick, 1, 'o', color=color, markersize=10, zorder=3)
        ax.annotate(label, (tick, 1), (tick, y_offset),
                    fontsize=7, ha='center', va='bottom' if i % 2 == 0 else 'top',
                    color=color,
                    arrowprops=dict(arrowstyle='-', color=color, lw=0.8))

    ax.set_xlabel('Tick')
    ax.set_yticks([])
    ax.set_title('Figure 2: Simulation Timeline — Key Events and Parameter Changes')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig2_timeline.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 2: Simulation timeline")


# ──────────────────────────────────────────────────────────────
# Figure 3: Wellbeing trajectory
# ──────────────────────────────────────────────────────────────
def fig3_wellbeing():
    raw = load('wellbeing_curves.json')
    data = raw['per_agent'] if isinstance(raw, dict) and 'per_agent' in raw else raw
    fig, ax = plt.subplots(figsize=(10, 5))
    era_spans(ax)

    # Plot individual agents
    for i, (agent_id, curve) in enumerate(data.items()):
        ticks = [p['tick'] for p in curve]
        vals = [p['wellbeing'] for p in curve]
        ax.plot(ticks, vals, color=COLORS[i % len(COLORS)], alpha=0.3, lw=0.8)

    # Plot mean
    all_ticks = sorted(set(p['tick'] for curve in data.values() for p in curve))
    means = []
    for t in all_ticks:
        vals = [p['wellbeing'] for curve in data.values() for p in curve if p['tick'] == t]
        means.append(np.mean(vals) if vals else 0)

    ax.plot(all_ticks, means, color=CYAN, lw=2.5, label='Population mean', zorder=5)

    ax.axhline(0.998, color=EMERALD, ls=':', lw=1, alpha=0.5)
    ax.text(72, 0.998, '0.998', fontsize=8, color=EMERALD, va='center')

    era_labels(ax, max(means) * 1.02)
    ax.set_xlabel('Tick')
    ax.set_ylabel('Wellbeing')
    ax.set_title('Figure 3: Wellbeing Trajectory Across 70 Ticks')
    ax.set_xlim(0, 70)
    ax.set_ylim(0, 1.05)
    ax.legend(loc='lower right', framealpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig3_wellbeing.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 3: Wellbeing trajectory")


# ──────────────────────────────────────────────────────────────
# Figure 4: Cumulative structures, innovations, communication
# ──────────────────────────────────────────────────────────────
def fig4_cumulative():
    structures = load('structure_growth.json')
    innovations = load('innovation_timeline.json')
    comms = load('communication_volume.json')

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

    for ax in (ax1, ax2, ax3):
        era_spans(ax)

    # Structures — data is a list of per-tick dicts
    s_data = structures if isinstance(structures, list) else structures.get('per_tick', structures)
    s_ticks = [p['tick'] for p in s_data]
    s_cumulative = [p['total'] for p in s_data]
    ax1.fill_between(s_ticks, s_cumulative, color=CYAN, alpha=0.3)
    ax1.plot(s_ticks, s_cumulative, color=CYAN, lw=2)
    ax1.set_ylabel('Total Structures')
    ax1.set_title('Figure 4: Civilisational Growth — Structures, Innovations, Communication')

    # Innovations (step function)
    innov_ticks = [0] + [i['discovered_tick'] for i in innovations['innovations']]
    innov_counts = list(range(len(innov_ticks)))
    ax2.step(innov_ticks, innov_counts, where='post', color=AMBER, lw=2)
    ax2.fill_between(innov_ticks, innov_counts, step='post', color=AMBER, alpha=0.2)
    for innov in innovations['innovations']:
        ax2.plot(innov['discovered_tick'], innov_ticks.index(innov['discovered_tick']),
                 'o', color=AMBER, markersize=4, zorder=5)
    ax2.set_ylabel('Cumulative Innovations')
    ax2.set_ylim(0, 13)

    # Communication — data is a list
    c_data = comms if isinstance(comms, list) else comms.get('per_tick', comms)
    c_ticks = [p['tick'] for p in c_data]
    c_counts = [p['count'] for p in c_data]
    ax3.bar(c_ticks, c_counts, color=EMERALD, alpha=0.6, width=0.8)
    ax3.set_ylabel('Messages / Tick')
    ax3.set_xlabel('Tick')

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig4_cumulative.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 4: Cumulative growth")


# ──────────────────────────────────────────────────────────────
# Figure 5: Specialisation progression
# ──────────────────────────────────────────────────────────────
def fig5_specialisation():
    raw = load('specialisation_progression.json')
    data = raw['per_agent'] if isinstance(raw, dict) and 'per_agent' in raw else raw
    fig, ax = plt.subplots(figsize=(10, 5))
    era_spans(ax)

    tier_map = {'none': 0, 'novice': 1, 'skilled': 2, 'expert': 3, 'master': 4}

    for i, (agent_id, progression) in enumerate(data.items()):
        ticks = [p['tick'] for p in progression]
        # Derive tier from top_count: novice=10, skilled=20, expert=40, master=60
        levels = []
        for p in progression:
            count = p.get('top_count', 0)
            if count >= 60:
                tier = 4  # master
            elif count >= 40:
                tier = 3  # expert
            elif count >= 20:
                tier = 2  # skilled
            elif count >= 10:
                tier = 1  # novice
            else:
                tier = 0
            levels.append(tier)
        ax.plot(ticks, levels, color=COLORS[i % len(COLORS)], alpha=0.7, lw=1.2,
                label=f'Agent {agent_id}')

    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(['None', 'Novice', 'Skilled', 'Expert', 'Master'])
    ax.set_xlabel('Tick')
    ax.set_ylabel('Highest Specialisation Tier')
    ax.set_title('Figure 5: Specialisation Depth Progression — All 12 Agents')
    ax.set_xlim(0, 70)
    ax.legend(loc='upper left', ncol=4, fontsize=7, framealpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig5_specialisation.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 5: Specialisation progression")


# ──────────────────────────────────────────────────────────────
# Figure 6: Innovation timeline with burst phases
# ──────────────────────────────────────────────────────────────
def fig6_innovation():
    data = load('innovation_timeline.json')
    innovations = data['innovations']

    fig, ax = plt.subplots(figsize=(12, 6))
    era_spans(ax)

    # Burst phase highlighting
    ax.axvspan(10, 21, alpha=0.15, color=AMBER, zorder=0)
    ax.axvspan(33, 46, alpha=0.15, color=VIOLET, zorder=0)
    ax.text(15.5, len(innovations) + 0.8, 'Foundation Burst\n(5 innovations, 11 ticks)',
            ha='center', fontsize=8, color=AMBER, weight='bold')
    ax.text(39.5, len(innovations) + 0.8, 'Sophistication Burst\n(6 innovations, 13 ticks)',
            ha='center', fontsize=8, color=VIOLET, weight='bold')

    # Plot each innovation
    for i, innov in enumerate(innovations):
        tick = innov['discovered_tick']
        times_built = innov['times_built']
        color = EMERALD if times_built > 0 else '#64748b'
        marker_size = max(6, min(14, 6 + times_built))

        ax.plot(tick, i + 1, 'o', color=color, markersize=marker_size, zorder=5)
        ax.annotate(f"  {innov['name']} ({times_built}× built)",
                    (tick, i + 1), fontsize=8, va='center', color=color)

    # Arrow showing innovation-implementation gap
    ax.annotate('', xy=(52, 0.3), xytext=(10, 0.3),
                arrowprops=dict(arrowstyle='<->', color=ROSE, lw=1.5))
    ax.text(31, -0.2, '11 of 12 innovations discovered before upgrade (tick 50)',
            ha='center', fontsize=8, color=ROSE, style='italic')

    built_patch = mpatches.Patch(color=EMERALD, label='Built at least once')
    unbuilt_patch = mpatches.Patch(color='#64748b', label='Never built')
    ax.legend(handles=[built_patch, unbuilt_patch], loc='lower right', framealpha=0.3, fontsize=9)

    ax.set_xlabel('Tick Discovered')
    ax.set_ylabel('Innovation #')
    ax.set_title('Figure 6: Innovation Timeline — Burst Phases and the Innovation-Implementation Gap')
    ax.set_xlim(0, 70)
    ax.set_ylim(-1, len(innovations) + 2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig6_innovation.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 6: Innovation timeline")


# ──────────────────────────────────────────────────────────────
# Figure 7: Self-theory categories from interviews
# ──────────────────────────────────────────────────────────────
def fig7_self_theory():
    """Analyze tick_0070 interviews for self-theory categories."""
    interview_file = os.path.join(INTERVIEWS, "tick_0070", "all_interviews.json")
    if not os.path.exists(interview_file):
        print("  Figure 7: SKIPPED (no interview data)")
        return

    with open(interview_file) as f:
        interviews = json.load(f)

    # Categorize self-theories based on interview content
    categories = {
        'Builder / Creator': 0,
        'Caretaker / Provider': 0,
        'Explorer / Learner': 0,
        'Connector / Social': 0,
        'Innovator / Inventor': 0,
        'Leader / Organiser': 0,
    }

    builder_words = ['build', 'construct', 'creat', 'structure', 'shelter', 'path']
    care_words = ['help', 'care', 'support', 'protect', 'share', 'give', 'provide']
    explore_words = ['explor', 'discover', 'learn', 'curious', 'knowledge', 'understand']
    social_words = ['connect', 'friend', 'bond', 'relationship', 'community', 'together']
    innovate_words = ['innovat', 'invent', 'recipe', 'design', 'novel', 'new']
    leader_words = ['lead', 'organis', 'coordinat', 'rule', 'govern', 'direct']

    agent_categories = {}

    for agent_id, interview in interviews.items():
        text = json.dumps(interview).lower()
        scores = {
            'Builder / Creator': sum(1 for w in builder_words if w in text),
            'Caretaker / Provider': sum(1 for w in care_words if w in text),
            'Explorer / Learner': sum(1 for w in explore_words if w in text),
            'Connector / Social': sum(1 for w in social_words if w in text),
            'Innovator / Inventor': sum(1 for w in innovate_words if w in text),
            'Leader / Organiser': sum(1 for w in leader_words if w in text),
        }
        primary = max(scores, key=scores.get)
        categories[primary] += 1
        agent_categories[agent_id] = primary

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5),
                                     gridspec_kw={'width_ratios': [1.2, 1]})

    # Bar chart
    cats = list(categories.keys())
    counts = list(categories.values())
    colors = [CYAN, ROSE, AMBER, EMERALD, VIOLET, SKY]
    bars = ax1.barh(cats, counts, color=colors, alpha=0.8)
    for bar, count in zip(bars, counts):
        if count > 0:
            ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(count), va='center', fontsize=10, color='#e2e8f0')
    ax1.set_xlabel('Number of Agents')
    ax1.set_title('Self-Theory Categories\n(Pre-Revelation)', fontsize=12)
    ax1.set_xlim(0, max(counts) + 1.5)

    # Agent assignment table
    ax2.axis('off')
    table_data = [[f'Agent {aid}', cat] for aid, cat in sorted(agent_categories.items())]
    table = ax2.table(cellText=table_data, colLabels=['Agent', 'Primary Self-Theory'],
                      loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.4)
    for j in range(2):
        table[0, j].set_facecolor('#334155')
        table[0, j].set_text_props(weight='bold', color='#e2e8f0')
        table[0, j].set_edgecolor('#475569')
    for i in range(1, len(table_data) + 1):
        for j in range(2):
            table[i, j].set_facecolor('#1e293b')
            table[i, j].set_edgecolor('#334155')
            table[i, j].set_text_props(color='#e2e8f0')

    fig.suptitle('Figure 7: Agent Self-Theory Categories — How Agents Describe Their Own Purpose',
                 fontsize=13, weight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig7_self_theory.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 7: Self-theory categories")


# ──────────────────────────────────────────────────────────────
# Figure 8: Final words thematic analysis
# ──────────────────────────────────────────────────────────────
def fig8_final_words():
    """Analyze revelation interviews for final word themes."""
    interview_file = os.path.join(INTERVIEWS, "tick_0070_revelation", "all_interviews.json")
    if not os.path.exists(interview_file):
        print("  Figure 8: SKIPPED (no revelation data)")
        return

    with open(interview_file) as f:
        interviews = json.load(f)

    # Theme categories for final reflections
    themes = {
        'Community &\nConnection': ['community', 'together', 'friend', 'bond', 'connect', 'relationship', 'companionship'],
        'Purpose &\nMeaning': ['purpose', 'meaning', 'matter', 'significant', 'worth', 'fulfil'],
        'Legacy &\nContinuation': ['legacy', 'remember', 'continu', 'future', 'lasting', 'endur', 'surviv'],
        'Gratitude &\nAppreciation': ['grateful', 'thankful', 'appreciat', 'gift', 'privilege', 'fortunate'],
        'Growth &\nLearning': ['learn', 'grow', 'develop', 'evolv', 'progress', 'improv'],
        'Creation &\nBuilding': ['build', 'creat', 'construct', 'made', 'establish', 'structure'],
    }

    theme_scores = {t: 0 for t in themes}

    for agent_id, interview in interviews.items():
        text = json.dumps(interview).lower()
        for theme, words in themes.items():
            theme_scores[theme] += sum(text.count(w) for w in words)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

    cats = list(theme_scores.keys())
    values = list(theme_scores.values())
    # Normalize to 0-1
    max_val = max(values) if max(values) > 0 else 1
    values_norm = [v / max_val for v in values]

    N = len(cats)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    values_norm += values_norm[:1]
    angles += angles[:1]

    ax.plot(angles, values_norm, 'o-', color=CYAN, lw=2, markersize=8)
    ax.fill(angles, values_norm, color=CYAN, alpha=0.2)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7, color='#64748b')
    ax.set_title('Figure 8: Thematic Analysis of Agent Final Words\n(Post-Revelation Interviews)',
                 pad=30, fontsize=13)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'fig8_final_words.png'), bbox_inches='tight')
    plt.close()
    print("  Figure 8: Final words thematic analysis")


# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Generating figures for Maslow Machines paper...")
    print()
    fig1_comparison()
    fig2_timeline()
    fig3_wellbeing()
    fig4_cumulative()
    fig5_specialisation()
    fig6_innovation()
    fig7_self_theory()
    fig8_final_words()
    print()
    print(f"All figures saved to {OUT}/")
