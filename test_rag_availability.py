"""
Quick test to verify RAG system loads patterns correctly
Shows available domains, content types, and priorities
"""
from rag_system import QuestionBookRAG

print("\n" + "="*80)
print("RAG SYSTEM - PATTERN AVAILABILITY TEST")
print("="*80 + "\n")

# Initialize RAG system (will use existing vectorstore if REBUILD=false)
rag = QuestionBookRAG()

print("\n" + "="*80)
print("PATTERN STATISTICS")
print("="*80 + "\n")

if not rag.questions:
    print("❌ ERROR: No patterns loaded!")
    print("   This means RAG won't work - check logs above")
else:
    print(f"✅ Total patterns available: {len(rag.questions)}")
    
    # Content types
    content_types = {}
    for q in rag.questions:
        ctype = q.get('content_type', 'unknown')
        content_types[ctype] = content_types.get(ctype, 0) + 1
    
    print(f"\n📋 Content Types:")
    for ctype, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {ctype}: {count}")
    
    # Priorities
    priorities = {}
    for q in rag.questions:
        priority = q.get('priority', 'NORMAL')
        priorities[priority] = priorities.get(priority, 0) + 1
    
    print(f"\n⚡ Priority Distribution:")
    for priority in ['CRITICAL', 'HIGH', 'NORMAL', 'LOW']:
        count = priorities.get(priority, 0)
        if count > 0:
            print(f"   - {priority}: {count}")
    
    # Domains
    domains = {}
    for q in rag.questions:
        domain = q.get('medical_domain', 'Unknown')
        if domain:
            domains[domain] = domains.get(domain, 0) + 1
    
    print(f"\n🏥 Medical Domains ({len(domains)} total):")
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {domain}: {count}")

# Test semantic search availability
print("\n" + "="*80)
print("VECTORSTORE STATUS")
print("="*80 + "\n")

if rag.collection:
    count = rag.collection.count()
    print(f"✅ Vectorstore active: {count} embeddings")
    print(f"   Semantic search: ENABLED")
else:
    print(f"❌ Vectorstore not available")
    print(f"   Semantic search: DISABLED (using keyword search only)")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80 + "\n")

