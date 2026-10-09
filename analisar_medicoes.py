#!/usr/bin/env python3
"""Uso: python3 analisar_medicoes.py measurements_resumed.csv --output resultados
Dependências: numpy, pandas, scipy e matplotlib.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

REGIONS={'full':'Full Picture','seahorse':'Seahorse Valley','elephant':'Elephant Valley','triple_spiral':'Triple Spiral Valley'}
THREADS=[1,2,4,8,16,32]
COLORS=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',type=Path)
    parser.add_argument('--output',type=Path,default=Path('resultados'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(args.csv)
    keys=['version','region','size','threads','mode']
    expected=set()
    for region in REGIONS:
        for n in [2**p for p in range(4,14)]:
            for v,th,mode in [('seq',1,'full'),('seq',1,'compute')]+[(v,th,'compute') for th in THREADS for v in ['omp','pth']]:
                for r in range(1,11):expected.add((v,region,n,th,mode,r))
    actual=list(df[keys+['repetition']].itertuples(index=False,name=None))
    if len(actual)!=5600 or len(set(actual))!=5600 or set(actual)!=expected:
        raise ValueError('CSV incompleto, duplicado ou com configurações inesperadas.')
    if not np.isfinite(df.seconds).all() or not (df.seconds>0).all():raise ValueError('Tempos inválidos.')
    s=df.groupby(keys,sort=False).seconds.agg(n='count',mean_s='mean',sd_s='std',median_s='median',min_s='min',max_s='max').reset_index()
    s['ci95_half_s']=t.ppf(.975,s.n-1)*s.sd_s/np.sqrt(s.n)
    s['ci95_low_s']=s.mean_s-s.ci95_half_s;s['ci95_high_s']=s.mean_s+s.ci95_half_s
    s['cv_percent']=100*s.sd_s/s.mean_s
    s.to_csv(args.output/'estatisticas.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titlesize':12,'figure.facecolor':'white','savefig.facecolor':'white'})
    def series(ax,sub,x,label,color,style='-'):
        sub=sub.sort_values(x)
        ax.errorbar(sub[x],sub.mean_s,yerr=sub.ci95_half_s,label=label,color=color,marker='o',markersize=3,linewidth=1.35,linestyle=style,capsize=2,elinewidth=.8)
    def decorate(ax):
        ax.grid(True,alpha=.22);ax.set_axisbelow(True)
    def save(fig,name):
        fig.savefig(args.output/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
    for index,(region,title) in enumerate(REGIONS.items(),1):
        fig,axes=plt.subplots(1,2,figsize=(13,5.2),sharey=True)
        for ax,v,label in zip(axes,['omp','pth'],['OpenMP','Pthreads']):
            sub=s[(s.region==region)&(s['mode']=='compute')]
            series(ax,sub[sub.version=='seq'],'size','Sequencial','#20242A','--')
            for th,color in zip(THREADS,COLORS):series(ax,sub[(sub.version==v)&(sub.threads==th)],'size',f'{th} thread'+('s' if th>1 else ''),color)
            ax.set_xscale('log',base=2);ax.set_xticks([16,64,256,1024,4096,8192]);ax.xaxis.set_major_formatter(ScalarFormatter())
            ax.set_yscale('symlog',linthresh=.001,linscale=1)
            ax.set_xlabel('Lado da imagem N (pixels)');ax.set_title(label);decorate(ax)
        axes[0].set_ylabel('Tempo médio (s) · symlog, faixa linear ±1 ms')
        handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=7,frameon=False,bbox_to_anchor=(.5,.03))
        fig.suptitle(f'{title} | tempo × tamanho, sem imagem',fontsize=15)
        fig.text(.5,.005,'Barras: IC 95% da média (t de Student, n = 10). Eixo y linear perto de zero e logarítmico fora dessa faixa.',ha='center',fontsize=9)
        fig.tight_layout(rect=(0,.12,1,.93));save(fig,f'0{index}_tamanho_{region}')
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,(region,title) in zip(axes.flat,REGIONS.items()):
        sub=s[(s.region==region)&(s['size']==8192)&(s['mode']=='compute')]
        for v,label,color in [('omp','OpenMP','#0072B2'),('pth','Pthreads','#D55E00')]:series(ax,sub[sub.version==v],'threads',label,color)
        seq=sub[sub.version=='seq'].iloc[0]
        ax.axhline(seq.mean_s,color='#303030',linestyle='--',label='Sequencial')
        ax.axhspan(seq.ci95_low_s,seq.ci95_high_s,color='#303030',alpha=.14)
        ax.set_xscale('log',base=2);ax.set_xticks(THREADS);ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.set_xlabel('Número de threads');ax.set_ylabel('Tempo médio (s)');ax.set_title(title);decorate(ax)
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False)
    fig.suptitle('Escalabilidade | N = 8192 · médias e IC 95%',fontsize=15);fig.tight_layout(rect=(0,.055,1,.95));save(fig,'05_threads_8192')
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,(region,title) in zip(axes.flat,REGIONS.items()):
        sub=s[(s.region==region)&(s.version=='seq')]
        for mode,label,color in [('full','Com imagem','#D55E00'),('compute','Sem imagem','#0072B2')]:series(ax,sub[sub['mode']==mode],'size',label,color)
        ax.set_xscale('log',base=2);ax.set_xticks([16,64,256,1024,4096,8192]);ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.set_yscale('symlog',linthresh=.001,linscale=1);ax.set_xlabel('Lado da imagem N (pixels)');ax.set_ylabel('Tempo médio (s) · symlog');ax.set_title(title);decorate(ax)
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.5,.025))
    fig.suptitle('Custo de produzir a imagem | sequencial · médias e IC 95%',fontsize=15)
    fig.text(.5,.006,'Symlog: faixa linear ±1 ms; preserva os limites negativos de ICs largos. Dados não foram filtrados.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.09,1,.95));save(fig,'06_custo_imagem')
    fig,ax=plt.subplots(figsize=(10,6))
    for (region,title),color in zip(REGIONS.items(),COLORS):
        sub=s[(s.region==region)&(s.version=='seq')&(s['mode']=='compute')]
        series(ax,sub,'size',title,color)
    ax.set_xscale('log',base=2);ax.set_yscale('log');ax.set_xticks([16,32,64,128,256,512,1024,2048,4096,8192]);ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.set_xlabel('Lado da imagem N (pixels)');ax.set_ylabel('Tempo médio (s) · escala logarítmica');decorate(ax);ax.legend(frameon=False)
    ax.set_title('Custo das regiões | sequencial sem imagem · médias e IC 95%')
    fig.tight_layout();save(fig,'07_regioes')
    summary=[]
    for region in REGIONS:
        sub=s[(s.region==region)&(s['size']==8192)]
        seq=sub[(sub.version=='seq')&(sub['mode']=='compute')].iloc[0]
        full=sub[(sub.version=='seq')&(sub['mode']=='full')].iloc[0]
        row={'region':region,'seq_compute_s':seq.mean_s,'seq_full_s':full.mean_s,'image_difference_s':full.mean_s-seq.mean_s,'image_difference_percent_full':100*(full.mean_s-seq.mean_s)/full.mean_s}
        for v in ['omp','pth']:
            best=sub[sub.version==v].sort_values('mean_s').iloc[0]
            row.update({f'{v}_best_threads':int(best.threads),f'{v}_best_s':best.mean_s,f'{v}_speedup':seq.mean_s/best.mean_s})
        summary.append(row)
    pd.DataFrame(summary).to_csv(args.output/'resumo_8192.csv',index=False)
    print(pd.DataFrame(summary).to_string(index=False))
    print(f'Gerados 7 gráficos e 2 tabelas em {args.output}.')
if __name__=='__main__':main()
