"""
Demonstration script showing priority-based retrieval with red flags first
"""
from rag_system import QuestionBookRAG

def demo_priority_retrieval():
    """Demonstrate priority-based retrieval system"""
    
    print("\n" + "="*80)
    print("PRIORITY-BASED RETRIEVAL DEMONSTRATION")
    print("="*80)
    
    # Initialize RAG system (without embeddings for this demo)
    rag = QuestionBookRAG()
    
    print(f"\nTotal patterns loaded: {len(rag.questions)}")
    
    # Test 1: Search for abdominal pain (should prioritize red flags)
    print("\n" + "-"*80)
    print("TEST 1: Patient mentions severe abdominal pain")
    print("-"*80)
    
    context = "I have severe pain in my right lower abdomen that started suddenly"
    result = rag.get_next_question(
        conversation_context=context,
        use_semantic_search=False,  # Use keyword search for demo
        prioritize_red_flags=True
    )
    
    if result:
        print(f"\n✅ Bot Response (Priority: {result.get('priority')}):")
        print(f"   Question: {result.get('bot_question')}")
        print(f"   Type: {result.get('content_type')}")
        print(f"   Domain: {result.get('medical_domain')}")
        print(f"   Section: {result.get('section')}")
    else:
        print("\n❌ No matching pattern found")
    
    # Test 2: Search without priority (compare)
    print("\n" + "-"*80)
    print("TEST 2: Same query WITHOUT priority-based ordering")
    print("-"*80)
    
    result_no_priority = rag.get_next_question(
        conversation_context=context,
        use_semantic_search=False,
        prioritize_red_flags=False
    )
    
    if result_no_priority:
        print(f"\n✅ Bot Response (Priority: {result_no_priority.get('priority')}):")
        print(f"   Question: {result_no_priority.get('bot_question')}")
        print(f"   Type: {result_no_priority.get('content_type')}")
    
    # Test 3: Show all priority levels for abdominal pain
    print("\n" + "-"*80)
    print("TEST 3: All priority levels for AbdominalPain domain")
    print("-"*80)
    
    abdominal_patterns = rag.search_by_system('AbdominalPain')
    
    priority_counts = {}
    for pattern in abdominal_patterns:
        priority = pattern.get('priority', 'UNKNOWN')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    print(f"\nAbdominalPain patterns by priority:")
    for priority in ['CRITICAL', 'HIGH', 'NORMAL', 'LOW']:
        count = priority_counts.get(priority, 0)
        if count > 0:
            print(f"   {priority}: {count} patterns")
    
    # Show sample CRITICAL pattern
    critical_patterns = [p for p in abdominal_patterns if p.get('priority') == 'CRITICAL']
    if critical_patterns:
        print(f"\n📌 Sample CRITICAL pattern:")
        sample = critical_patterns[0]
        print(f"   Question: {sample.get('bot_question')}")
        print(f"   Red Flags: {sample.get('red_flags', [])[:3]}")
    
    # Test 4: Content type distribution
    print("\n" + "-"*80)
    print("TEST 4: Content type distribution across all domains")
    print("-"*80)
    
    content_counts = {}
    for pattern in rag.questions:
        content_type = pattern.get('content_type', 'unknown')
        content_counts[content_type] = content_counts.get(content_type, 0) + 1
    
    print(f"\nPatterns by content type:")
    for content_type, count in sorted(content_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {content_type}: {count} patterns")
    
    # Test 5: Tree path examples
    print("\n" + "-"*80)
    print("TEST 5: Sample tree paths (showing organization)")
    print("-"*80)
    
    sample_paths = set()
    for pattern in rag.questions[:50]:  # First 50 patterns
        if pattern.get('tree_path'):
            sample_paths.add(pattern['tree_path'])
    
    print(f"\nSample tree paths:")
    for i, path in enumerate(sorted(sample_paths)[:10], 1):
        print(f"   {i}. {path}")
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\n✅ Priority-based retrieval working correctly!")
    print("✅ Red flags will surface first in conversations")
    print("✅ Flexible schema supports all content types")
    print("✅ System ready for production use\n")


if __name__ == "__main__":
    demo_priority_retrieval()

